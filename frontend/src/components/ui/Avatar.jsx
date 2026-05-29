import { mediaUrl, nameColor } from '../../hooks/useMediaUrl';

const AVATAR_COLORS = [
  '#e53935','#d81b60','#8e24aa','#5e35b1',
  '#1e88e5','#00acc1','#43a047','#fb8c00',
];

function getBgColor(name) {
  if (!name) return '#708499';
  let hash = 0;
  for (let c of name) hash = c.charCodeAt(0) + ((hash << 5) - hash);
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

export default function Avatar({ src, alt = '', size = 48, online = false, borderSrc = 'sidebar' }) {
  const url = mediaUrl(src);
  const initial = alt?.charAt(0)?.toUpperCase() || '?';
  const bg = getBgColor(alt);
  const fontSize = Math.round(size * 0.4);

  const borderStyle = `--bg-${borderSrc}`;

  return (
    <div
      className="avatar"
      style={{ width: size, height: size, minWidth: size, borderRadius: '50%' }}
    >
      {url ? (
        <img src={url} alt={alt} style={{ width: size, height: size }} />
      ) : (
        <div
          className="avatar-placeholder"
          style={{
            width: size,
            height: size,
            background: bg,
            fontSize,
          }}
        >
          {initial}
        </div>
      )}
      {online && (
        <div
          className="online-dot"
          style={{
            width: Math.max(10, size * 0.22),
            height: Math.max(10, size * 0.22),
          }}
        />
      )}
    </div>
  );
}
