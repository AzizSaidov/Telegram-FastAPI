import { formatSeparatorDate } from '../../hooks/useMediaUrl';

export default function DateSeparator({ date }) {
  return (
    <div className="date-separator">
      <span className="date-separator-badge">{formatSeparatorDate(date)}</span>
    </div>
  );
}
