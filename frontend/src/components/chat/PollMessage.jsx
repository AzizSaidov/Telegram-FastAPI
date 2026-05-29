import { useState } from 'react';
import { votePoll } from '../../api/polls';
import useAuthStore from '../../store/authStore';
import useChatStore from '../../store/chatStore';
import toast from 'react-hot-toast';

export default function PollMessage({ poll, messageId }) {
  const currentUser = useAuthStore((s) => s.user);
  const { updateMessage } = useChatStore();
  const [loading, setLoading] = useState(false);

  if (!poll) return null;

  const totalVotes = poll.options?.reduce((sum, o) => sum + (o.votes_count || 0), 0) || 0;
  const myVote = poll.options?.find(o => o.voters?.some(v => v.id === currentUser?.id));
  const hasVoted = !!myVote;

  const handleVote = async (optionId) => {
    if (hasVoted && !poll.is_multiple) return;
    setLoading(true);
    try {
      const res = await votePoll(poll.id, { option_id: optionId });
      updateMessage({ id: messageId, poll: res.data });
    } catch {
      toast.error('Ошибка при голосовании');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="poll-container">
      <div className="poll-question">{poll.question}</div>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10 }}>
        {poll.is_multiple ? '🔲 Несколько вариантов' : '🔘 Один вариант'} · {totalVotes} {totalVotes === 1 ? 'голос' : totalVotes < 5 ? 'голоса' : 'голосов'}
      </div>

      {poll.options?.map((option) => {
        const pct = totalVotes > 0 ? Math.round((option.votes_count || 0) / totalVotes * 100) : 0;
        const isMyChoice = option.voters?.some(v => v.id === currentUser?.id);
        const isWinning = option.votes_count === Math.max(...(poll.options?.map(o => o.votes_count || 0) || [0])) && option.votes_count > 0;

        return (
          <div
            key={option.id}
            className={`poll-option${isMyChoice ? ' chosen' : ''}${hasVoted || loading ? ' voted' : ''}`}
            onClick={() => !loading && handleVote(option.id)}
          >
            <div className="poll-option-bar" style={{ width: hasVoted ? `${pct}%` : '0%', background: isMyChoice ? 'var(--accent)' : 'var(--bg-hover)' }} />
            <div className="poll-option-content">
              <span className="poll-option-text">{option.text}</span>
              {hasVoted && (
                <span className="poll-option-pct">{pct}%</span>
              )}
              {isMyChoice && (
                <span style={{ marginLeft: 4, color: 'var(--accent)' }}>✓</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
