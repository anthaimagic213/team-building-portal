import { FormEvent, useState } from 'react';
import { notificationApi } from '@/api';

export default function NotificationsPage() {
  const [eventId, setEventId] = useState('');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [type, setType] = useState('INFO');

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      await notificationApi.createNotification({
        event_id: eventId,
        title,
        content,
        notification_type: type,
      });

      setMessage('Tạo thông báo thành công.');
      setTitle('');
      setContent('');
    } catch {
      setMessage('Không thể tạo thông báo.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-container">
      <h1 className="text-2xl font-bold text-slate-900">
        Gửi thông báo
      </h1>

      <section className="card mt-6 max-w-2xl p-6">
        <form onSubmit={submit} className="space-y-5">
          <label className="block">
            <span className="form-label">Event ID</span>
            <input
              className="input"
              required
              value={eventId}
              onChange={(event) =>
                setEventId(event.target.value)
              }
            />
          </label>

          <label className="block">
            <span className="form-label">Loại thông báo</span>
            <select
              className="input"
              value={type}
              onChange={(event) =>
                setType(event.target.value)
              }
            >
              <option value="INFO">Thông tin</option>
              <option value="WARNING">Cảnh báo</option>
              <option value="URGENT">Khẩn cấp</option>
            </select>
          </label>

          <label className="block">
            <span className="form-label">Tiêu đề</span>
            <input
              className="input"
              required
              value={title}
              onChange={(event) =>
                setTitle(event.target.value)
              }
            />
          </label>

          <label className="block">
            <span className="form-label">Nội dung</span>
            <textarea
              className="input min-h-32"
              required
              value={content}
              onChange={(event) =>
                setContent(event.target.value)
              }
            />
          </label>

          <button
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'Đang gửi...' : 'Tạo thông báo'}
          </button>

          {message && (
            <p className="text-sm text-blue-600">
              {message}
            </p>
          )}
        </form>
      </section>
    </div>
  );
}
