import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  requestLoginOTP,
  requestRegisterOTP,
  verifyLoginOTP,
  verifyRegisterOTP,
} from '../api/auth';
import useAuthStore from '../store/authStore';

const MODE_LOGIN = 'login';
const MODE_REGISTER = 'register';
const STEP_DETAILS = 'details';
const STEP_OTP = 'otp';
const RESEND_SECONDS = 45;

function TelegramMark() {
  return (
    <svg className="auth-mark" viewBox="0 0 240 240" aria-hidden="true">
      <defs>
        <linearGradient id="authTelegramGradient" x1="35" y1="10" x2="190" y2="220">
          <stop offset="0" stopColor="#37b7f7" />
          <stop offset="1" stopColor="#1d8ad6" />
        </linearGradient>
      </defs>
      <circle cx="120" cy="120" r="120" fill="url(#authTelegramGradient)" />
      <path
        fill="#fff"
        d="M184.3 69.2c4.2-1.7 8.1 2.2 6.8 6.7l-29.5 101.8c-1.4 5-7.3 6.9-11.3 3.7l-43.8-34.4-22.7 22c-3.1 3-8.3 1.5-9.3-2.7l-10.1-40.8-36.6-11.8c-4.9-1.6-5.2-8.4-.4-10.4L184.3 69.2Zm-29.6 31.2-68.2 31.8 8.1 30 5.2-22.4c.4-1.8 1.5-3.3 3-4.3l51.9-35.1Z"
      />
    </svg>
  );
}

function getApiMessage(error, fallback) {
  if (!error?.response) {
    return 'Нет соединения с backend. Проверьте, что http://127.0.0.1:8000 запущен.';
  }

  const detail = error?.response?.data?.detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || String(item)).join(', ');
  }

  const message = detail || fallback;
  const dictionary = {
    'User not found. Please register first': 'Номер не найден. Зарегистрируйтесь.',
    'Phone number is already registered': 'Этот номер уже зарегистрирован. Войдите.',
    'Username is already taken': 'Username уже занят.',
    'Invalid or expired OTP code': 'Неверный или истекший код.',
    'Phone number must start with +': 'Номер должен начинаться с +.',
    'Phone number must contain 9-20 digits after +': 'Номер должен содержать от 9 до 20 цифр после +.',
  };

  return dictionary[message] || message;
}

function normalizePhone(value) {
  const raw = value.trim();
  const digits = raw.replace(/\D/g, '');

  if (!digits) return '';
  if (digits.length === 9) return `+992${digits}`;
  if (digits.length === 12 && digits.startsWith('992')) return `+${digits}`;
  if (raw.startsWith('+')) return `+${digits}`;

  return `+${digits}`;
}

function usernameValue(value) {
  const username = value.trim().replace(/^@+/, '').toLowerCase();
  return username || undefined;
}

export default function AuthPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [mode, setMode] = useState(MODE_LOGIN);
  const [step, setStep] = useState(STEP_DETAILS);
  const [phone, setPhone] = useState('');
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [otp, setOtp] = useState('');
  const [devCode, setDevCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendIn, setResendIn] = useState(0);

  const normalizedPhone = useMemo(() => normalizePhone(phone), [phone]);
  const isRegister = mode === MODE_REGISTER;

  useEffect(() => {
    if (!resendIn) return undefined;

    const timer = window.setInterval(() => {
      setResendIn((value) => Math.max(0, value - 1));
    }, 1000);

    return () => window.clearInterval(timer);
  }, [resendIn]);

  const resetFlow = (nextMode = mode) => {
    setMode(nextMode);
    setStep(STEP_DETAILS);
    setOtp('');
    setDevCode('');
    setError('');
    setResendIn(0);
  };

  const buildRegisterPayload = () => ({
    phone_number: normalizedPhone,
    full_name: fullName.trim(),
    username: usernameValue(username),
  });

  const validateDetails = () => {
    if (!normalizedPhone || !normalizedPhone.startsWith('+') || normalizedPhone.length < 10) {
      setError('Введите номер в формате +992...');
      return false;
    }

    if (isRegister && fullName.trim().length < 2) {
      setError('Введите имя для регистрации');
      return false;
    }

    return true;
  };

  const requestCode = async () => {
    if (!validateDetails()) return;

    setLoading(true);
    setError('');

    try {
      const payload = isRegister ? buildRegisterPayload() : { phone_number: normalizedPhone };
      const response = isRegister
        ? await requestRegisterOTP(payload)
        : await requestLoginOTP(payload);

      setPhone(normalizedPhone);
      setDevCode(response.data?.otp_code || '');
      setOtp('');
      setStep(STEP_OTP);
      setResendIn(RESEND_SECONDS);
    } catch (requestError) {
      const fallback = isRegister
        ? 'Не удалось отправить код регистрации'
        : 'Не удалось отправить код входа';
      setError(getApiMessage(requestError, fallback));
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async () => {
    if (otp.length !== 6) {
      setError('Введите 6-значный код');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const payload = isRegister
        ? { ...buildRegisterPayload(), otp_code: otp }
        : { phone_number: normalizedPhone, otp_code: otp };
      const response = isRegister
        ? await verifyRegisterOTP(payload)
        : await verifyLoginOTP(payload);
      const { user, access_token: accessToken, refresh_token: refreshToken } = response.data;

      setAuth(user, accessToken, refreshToken);
      toast.success(isRegister ? 'Аккаунт создан' : 'Вы вошли');
      navigate('/');
    } catch (requestError) {
      setError(getApiMessage(requestError, 'Неверный или истекший код'));
    } finally {
      setLoading(false);
    }
  };

  const submit = (event) => {
    event.preventDefault();

    if (step === STEP_OTP) {
      verifyCode();
      return;
    }

    requestCode();
  };

  const switchToRegister = () => {
    resetFlow(MODE_REGISTER);
  };

  const switchToLogin = () => {
    resetFlow(MODE_LOGIN);
  };

  return (
    <main className="auth-page">
      <section className="auth-panel" aria-label="Telegram auth">
        <TelegramMark />

        <div className="auth-heading">
          <h1>{isRegister ? 'Создать аккаунт' : 'Войти в Telegram'}</h1>
          <p>
            {isRegister
              ? 'Заполните данные и подтвердите номер кодом'
              : 'Введите номер уже зарегистрированного аккаунта'}
          </p>
        </div>

        <div className="auth-tabs" role="tablist" aria-label="Способ авторизации">
          <button
            type="button"
            role="tab"
            aria-selected={!isRegister}
            className={!isRegister ? 'active' : ''}
            onClick={switchToLogin}
          >
            Вход
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={isRegister}
            className={isRegister ? 'active' : ''}
            onClick={switchToRegister}
          >
            Регистрация
          </button>
        </div>

        <form className="auth-form" onSubmit={submit} autoComplete="off" noValidate>
          <input
            className="auth-autofill-trap"
            type="text"
            name="username"
            autoComplete="username"
            tabIndex={-1}
            aria-hidden="true"
          />
          <input
            className="auth-autofill-trap"
            type="password"
            name="password"
            autoComplete="current-password"
            tabIndex={-1}
            aria-hidden="true"
          />

          {step === STEP_DETAILS && (
            <>
              <label className="field">
                <span>Телефон</span>
                <input
                  value={phone}
                  onChange={(event) => {
                    setPhone(event.target.value);
                    setError('');
                  }}
                  placeholder="+992 90 000 00 00"
                  name="tg_manual_phone_number"
                  autoComplete="new-password"
                  inputMode="tel"
                  data-lpignore="true"
                  data-1p-ignore="true"
                  data-bwignore="true"
                  data-form-type="other"
                  autoFocus
                />
              </label>

              {isRegister && (
                <>
                  <label className="field">
                    <span>Имя</span>
                    <input
                      value={fullName}
                      onChange={(event) => {
                        setFullName(event.target.value);
                        setError('');
                      }}
                      placeholder="Имя и фамилия"
                      name="tg_manual_full_name"
                      autoComplete="new-password"
                      data-lpignore="true"
                      data-1p-ignore="true"
                      data-bwignore="true"
                      data-form-type="other"
                      maxLength={100}
                    />
                  </label>

                  <label className="field">
                    <span>Username</span>
                    <input
                      value={username}
                      onChange={(event) => {
                        setUsername(event.target.value);
                        setError('');
                      }}
                      placeholder="@username"
                      name="tg_manual_public_name"
                      autoComplete="new-password"
                      data-lpignore="true"
                      data-1p-ignore="true"
                      data-bwignore="true"
                      data-form-type="other"
                      maxLength={31}
                    />
                  </label>
                </>
              )}
            </>
          )}

          {step === STEP_OTP && (
            <>
              <div className="auth-step-card">
                <span>{isRegister ? 'Регистрация' : 'Вход'}</span>
                <strong>{normalizedPhone}</strong>
              </div>

              {devCode && (
                <button
                  type="button"
                  className="otp-card"
                  onClick={() => {
                    setOtp(devCode);
                    setError('');
                  }}
                  title="Подставить код"
                >
                  <span>Код</span>
                  <strong>{devCode}</strong>
                </button>
              )}

              <label className="field">
                <span>Код подтверждения</span>
                <input
                  className="otp-input"
                  value={otp}
                  onChange={(event) => {
                    setOtp(event.target.value.replace(/\D/g, '').slice(0, 6));
                    setError('');
                  }}
                  inputMode="numeric"
                  placeholder="000000"
                  autoComplete="one-time-code"
                  autoFocus
                />
              </label>
            </>
          )}

          {error && (
            <div className="form-error">
              {error}
              {!isRegister && String(error).toLowerCase().includes('зарегистр') && (
                <button type="button" onClick={switchToRegister}>
                  Зарегистрироваться
                </button>
              )}
              {isRegister && String(error).toLowerCase().includes('уже зарегистр') && (
                <button type="button" onClick={switchToLogin}>
                  Войти
                </button>
              )}
            </div>
          )}

          <button
            className="primary-button"
            disabled={
              loading
              || (step === STEP_DETAILS && (!phone.trim() || (isRegister && !fullName.trim())))
              || (step === STEP_OTP && otp.length !== 6)
            }
          >
            {loading && <span className="button-spinner" aria-hidden="true" />}
            {!loading && step === STEP_DETAILS && 'Получить код'}
            {!loading && step === STEP_OTP && (isRegister ? 'Создать аккаунт' : 'Войти')}
            {loading && (step === STEP_DETAILS ? 'Отправка...' : 'Проверка...')}
          </button>

          {step === STEP_OTP && (
            <div className="auth-actions">
              <button
                className="ghost-button"
                type="button"
                onClick={() => {
                  setStep(STEP_DETAILS);
                  setOtp('');
                  setDevCode('');
                  setError('');
                }}
              >
                Изменить номер
              </button>
              <button
                className="ghost-button"
                type="button"
                disabled={loading || resendIn > 0}
                onClick={requestCode}
              >
                {resendIn > 0 ? `Повторить через ${resendIn}` : 'Отправить еще раз'}
              </button>
            </div>
          )}
        </form>
      </section>
    </main>
  );
}
