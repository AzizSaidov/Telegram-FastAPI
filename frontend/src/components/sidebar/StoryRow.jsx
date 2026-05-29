import { useEffect, useState } from 'react';
import Avatar from '../ui/Avatar';
import useAuthStore from '../../store/authStore';
import useUIStore from '../../store/uiStore';
import { getStories, createStory } from '../../api/stories';

export default function StoryRow() {
  const currentUser = useAuthStore((s) => s.user);
  const [storyGroups, setStoryGroups] = useState([]);
  const fileRef = { current: null };

  useEffect(() => {
    getStories().then(r => setStoryGroups(r.data)).catch(() => {});
  }, []);

  const handleAddStory = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('media', file);
    try {
      await createStory(fd);
      const r = await getStories();
      setStoryGroups(r.data);
    } catch {}
  };

  const myGroup = storyGroups.find(g => g.user.id === currentUser?.id);
  const others  = storyGroups.filter(g => g.user.id !== currentUser?.id);

  return (
    <div className="stories-row">
      {/* Мои сторис */}
      <div
        className="story-circle"
        onClick={() => { if (!myGroup) document.getElementById('story-upload').click(); }}
      >
        <div className={`story-ring${myGroup ? '' : ' add'}`}>
          <div className="story-ring-inner">
            <Avatar
              src={currentUser?.profile?.avatar_url}
              alt={currentUser?.profile?.full_name}
              size={52}
            />
          </div>
          {!myGroup && (
            <div className="story-add-icon">+</div>
          )}
        </div>
        <span className="story-name">
          {myGroup ? 'Ваша' : 'Добавить'}
        </span>
        <input
          id="story-upload"
          type="file"
          accept="image/*,video/*"
          style={{ display: 'none' }}
          onChange={handleAddStory}
        />
      </div>

      {/* Чужие сторис */}
      {others.map((group) => {
        const allSeen = false; // TODO: отслеживать просмотры
        return (
          <div key={group.user.id} className="story-circle">
            <div className={`story-ring${allSeen ? ' seen' : ''}`}>
              <div className="story-ring-inner">
                <Avatar
                  src={group.user.profile?.avatar_url}
                  alt={group.user.profile?.full_name}
                  size={52}
                />
              </div>
            </div>
            <span className="story-name">
              {group.user.profile?.full_name?.split(' ')[0]}
            </span>
          </div>
        );
      })}
    </div>
  );
}
