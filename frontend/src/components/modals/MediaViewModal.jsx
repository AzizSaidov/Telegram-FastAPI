import useUIStore from '../../store/uiStore';
import { mediaUrl } from '../../hooks/useMediaUrl';

export default function MediaViewModal() {
  const { mediaView, clearMediaView } = useUIStore();
  if (!mediaView) return null;

  const isVideo = mediaView.match(/\.(mp4|webm|ogg|mov)$/i);
  const src = mediaUrl(mediaView) || mediaView;

  return (
    <div
      className="media-view-overlay"
      onClick={clearMediaView}
    >
      {/* Header */}
      <div className="media-view-header" onClick={e => e.stopPropagation()}>
        <button
          onClick={clearMediaView}
          style={{ color: '#fff', fontSize: 24, marginLeft: 'auto' }}
        >
          ✕
        </button>
      </div>

      {/* Media */}
      <div className="media-view-body" onClick={e => e.stopPropagation()}>
        {isVideo ? (
          <video src={src} controls autoPlay style={{ maxHeight: '80vh', maxWidth: '90%', borderRadius: 12 }} />
        ) : (
          <img src={src} alt="media" style={{ maxHeight: '80vh', maxWidth: '90%', objectFit: 'contain', borderRadius: 12 }} />
        )}
      </div>
    </div>
  );
}
