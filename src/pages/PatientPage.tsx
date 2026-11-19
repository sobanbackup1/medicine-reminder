import { useEffect, useMemo, useState } from 'react';
import { api, type PatientCalendarDay, type TodayStatus } from '@/api';

type DisplayStatus = 'taken' | 'forgot' | 'missed' | 'pending' | 'due';

const statusLabels: Record<DisplayStatus, string> = {
  taken: '服用済み',
  forgot: '忘れ',
  missed: '飲み忘れ',
  pending: '予定',
  due: '服用時間',
};

function localDate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
}

function isoLocal(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function previewCalendar(): PatientCalendarDay[] {
  const today = new Date();
  return Array.from({ length: 28 }, (_, index) => {
    const day = new Date(today);
    day.setDate(today.getDate() - 27 + index);
    return { log_date: isoLocal(day), status: null, action_timestamp: null };
  });
}

function dateText(value: string): string {
  return localDate(value).toLocaleDateString('ja-JP', {
    weekday: 'long', month: 'long', day: 'numeric',
  });
}

function timeText(value: string | null): string {
  return value
    ? new Date(value).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    : '';
}

function actionMessage(status: DisplayStatus, data: TodayStatus | null): string {
  if (status === 'taken') return `${timeText(data?.action_timestamp || null)}に服用済みです。`;
  if (status === 'forgot') return '「忘れた」として記録しました。通知を停止しました。';
  if (status === 'missed') return '飲み忘れとして記録しました。必要なら取り消せます。';
  if (status === 'due') return `服用時間です。予定時刻：${data?.medication_time || '—'}。`;
  return `まだ服用時間前です。予定時刻：${data?.medication_time || '—'}。`;
}

export default function PatientPage() {
  const [data, setData] = useState<TodayStatus | null>(null);
  const [calendar, setCalendar] = useState<PatientCalendarDay[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const load = async () => {
    try {
      const [today, history] = await Promise.all([
        api.getToday(),
        api.getPatientCalendar(28),
      ]);
      setData(today);
      setCalendar(history);
      setSelectedDate((previous) => previous || today.log_date);
      setError('');
    } catch {
      const preview = previewCalendar();
      setCalendar(preview);
      setSelectedDate(preview[preview.length - 1].log_date);
      setError('');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 30000);
    return () => window.clearInterval(timer);
  }, []);

  const selected = useMemo(
    () => calendar.find((day) => day.log_date === selectedDate) || null,
    [calendar, selectedDate],
  );

  const todayStatus: DisplayStatus = data?.status === 'pending' ? 'due' : (data?.status || 'pending');
  const isTodaySelected = Boolean(data && selectedDate === data.log_date);
  const selectedStatus: DisplayStatus = selected?.status || (isTodaySelected ? todayStatus : 'pending');
  const selectedLabel = selected ? dateText(selected.log_date) : data ? dateText(data.log_date) : '';

  const stats = useMemo(() => ({
    taken: calendar.filter((day) => day.status === 'taken').length,
    forgot: calendar.filter((day) => day.status === 'forgot').length,
    missed: calendar.filter((day) => day.status === 'missed').length,
    recorded: calendar.filter((day) => day.status && day.status !== 'pending').length,
  }), [calendar]);

  const act = async (action: 'taken' | 'forgot' | 'missed' | 'undo') => {
    setActing(true);
    setError('');
    setSuccess('');
    try {
      const result = action === 'missed'
        ? await api.markMissed()
        : action === 'undo'
          ? await api.undoToday()
          : await api.recordAction(action);
      setData(result);
      setSuccess(action === 'undo' ? '今日の記録を取り消しました。' : '今日の服用を記録しました。');
      setCalendar(await api.getPatientCalendar(28));
    } catch (e: any) {
      setError(e?.message || 'Action failed.');
      await load();
    } finally {
      setActing(false);
    }
  };

  if (loading) return <div className="pill-loading">Loading pill sheet…</div>;

  return (
    <>
      <style>{`
        :root { color-scheme: dark; }
        .pill-page { min-height: 100vh; background: #171b20; color: #e8ece6; padding: 18px 12px 32px; font-family: "Zen Maru Gothic", "Hiragino Maru Gothic ProN", system-ui, sans-serif; }
        .pill-main { width: min(100%, 720px); margin: 0 auto; display: flex; flex-direction: column; }
        .pill-title { order: 1; margin: 0 6px 14px; font-size: clamp(1.7rem, 6vw, 2.7rem); line-height: 1.05; letter-spacing: -.04em; }
        .pill-sheet { order: 3; overflow: hidden; border-radius: 24px; background: #2a2c24; box-shadow: 0 10px 28px rgba(0,0,0,.25); }
        .pill-weekdays { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; padding: 14px 12px; background: #49b873; }
        .pill-weekday { padding: 10px 4px; border-radius: 12px; background: #34362b; color: #49b873; text-align: center; font-weight: 800; font-size: clamp(.75rem, 2.4vw, 1rem); }
        .pill-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 14px 4px; padding: 18px 12px 22px; }
        .pill-week-label { grid-column: 1 / -1; margin: 0 4px -10px; color: #a3ada6; font-size: 1.1rem; font-weight: 800; }
        .pill-cell { display: flex; min-width: 0; flex-direction: column; align-items: center; gap: 5px; }
        .pill-number { align-self: flex-start; padding-left: 8px; color: #a3ada6; font-size: .9rem; }
        .pill-cell.today .pill-number { color: #49b873; font-weight: 900; }
        .pill-button { width: min(100%, 78px); aspect-ratio: 1; position: relative; display: grid; place-items: center; border: 3px solid #6b6f66; border-radius: 50%; background: radial-gradient(circle at 35% 30%, rgba(255,255,255,.32), rgba(255,255,255,.06) 55%), #4a4d49; color: #e8ece6; cursor: pointer; box-shadow: inset 0 2px 5px rgba(0,0,0,.2); }
        .pill-button:hover { border-color: #49b873; }
        .pill-button:focus-visible { outline: 3px solid #49b873; outline-offset: 3px; }
        .pill-button .tablet { width: 58%; height: 58%; display: grid; place-items: center; border-radius: 50%; background: #c98a8c; color: rgba(70,30,35,.6); font-size: .72rem; font-weight: 900; }
        .pill-button.final .tablet { background: #f1f2f0; color: rgba(70,70,70,.55); }
        .pill-button.taken::after { content: "✓"; color: #49b873; font-size: 2.6rem; font-weight: 900; }
        .pill-button.taken .tablet, .pill-button.forgot .tablet { display: none; }
        .pill-button.forgot { border-color: #e0a021; }
        .pill-button.forgot::after { content: "!"; color: #e0a021; font-size: 2.4rem; font-weight: 900; }
        .pill-button.missed { border-color: #c9453f; }
        .pill-button.missed::after { content: "×"; color: #c9453f; font-size: 2.5rem; font-weight: 900; }
        .pill-button.due { border-color: #49b873; box-shadow: 0 0 0 5px rgba(73,184,115,.2); }
        .pill-summary { order: 4; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 18px 0; }
        .pill-stat { border-radius: 16px; background: #34362b; padding: 14px 6px; color: #a3ada6; text-align: center; }
        .pill-stat strong { display: block; color: #e8ece6; font-size: 1.5rem; }
        .pill-legend { order: 5; display: flex; flex-wrap: wrap; gap: 8px 16px; margin: 0 6px 18px; color: #a3ada6; font-size: .85rem; }
        .pill-legend span::before { content: ""; display: inline-block; width: 11px; height: 11px; margin-right: 5px; border: 3px solid #6b6f66; border-radius: 50%; vertical-align: -1px; }
        .pill-legend .taken::before { border-color: #49b873; }
        .pill-legend .forgot::before { border-color: #e0a021; }
        .pill-legend .missed::before { border-color: #c9453f; }
        .pill-panel { order: 2; border-radius: 18px; background: #34362b; padding: 16px; margin-bottom: 14px; }
        .pill-panel h2 { margin: 0 0 6px; font-size: 1.25rem; }
        .pill-panel p { margin: 0 0 16px; color: #a3ada6; }
        .pill-actions { display: flex; flex-wrap: wrap; gap: 10px; }
        .pill-action { border: 0; border-radius: 12px; padding: 12px 16px; color: #fff; font: inherit; font-weight: 800; cursor: pointer; }
        .pill-action:disabled { cursor: not-allowed; opacity: .45; }
        .pill-action.taken { background: #2f8c55; }
        .pill-action.forgot { background: #8b6a15; }
        .pill-action.missed { background: #a83e39; }
        .pill-action.undo { background: #59605a; }
        .pill-alert { margin: 0 0 16px; border-radius: 12px; padding: 12px 14px; background: #5e2d2b; color: #ffd8d5; }
        .pill-success { margin: 0 0 16px; border-radius: 12px; padding: 12px 14px; background: #245b3b; color: #d9ffe5; }
        .pill-loading { min-height: 100vh; display: grid; place-items: center; background: #171b20; color: #e8ece6; font: 1.1rem system-ui; }
        @media (max-width: 520px) { .pill-page { padding: 12px 8px 24px; } .pill-weekdays, .pill-grid { padding-inline: 8px; gap: 4px; } .pill-grid { gap: 10px 1px; } .pill-button { width: min(100%, 44px); border-width: 2px; } .pill-button .tablet { font-size: .48rem; } .pill-button.taken::after, .pill-button.forgot::after, .pill-button.missed::after { font-size: 1.55rem; } .pill-summary { gap: 5px; margin: 12px 0; } .pill-stat { padding: 10px 3px; font-size: .68rem; } .pill-stat strong { font-size: 1.05rem; } .pill-action { width: 100%; padding: 10px 12px; } }
      `}</style>
      <main className="pill-page">
        <div className="pill-main">
          <h1 className="pill-title">{data?.medicine_name && data.medicine_name !== 'Medication' ? data.medicine_name : 'お薬シート'}</h1>

          <section className="pill-sheet" aria-label="Recent medication history">
            <div className="pill-weekdays">
              {calendar.slice(0, 7).map((day) => (
                <div className="pill-weekday" key={day.log_date}>
                  {localDate(day.log_date).toLocaleDateString('ja-JP', { weekday: 'short' })}
                </div>
              ))}
            </div>
            <div className="pill-grid">
              {calendar.map((day, index) => {
                const isToday = day.log_date === data?.log_date;
                const status: DisplayStatus = day.status || (isToday ? todayStatus : 'pending');
                return (
                  <div className={`pill-cell${isToday ? ' today' : ''}`} key={day.log_date}>
                    <span className="pill-number">{localDate(day.log_date).getDate()}</span>
                    <button
                      className={`pill-button ${status}${index >= calendar.length - 4 ? ' final' : ''}`}
                      aria-label={`${dateText(day.log_date)}: ${statusLabels[status]}`}
                      onClick={() => setSelectedDate(day.log_date)}
                    >
                      <span className="tablet">AK</span>
                    </button>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="pill-summary" aria-label="28日間の集計">
            <div className="pill-stat"><strong>{stats.recorded}</strong>記録済み</div>
            <div className="pill-stat"><strong>{stats.taken}</strong>服用済み</div>
            <div className="pill-stat"><strong>{stats.forgot}</strong>忘れ</div>
            <div className="pill-stat"><strong>{stats.missed}</strong>飲み忘れ</div>
          </section>

          <div className="pill-legend" aria-label="色の説明">
            <span>予定</span><span className="taken">服用済み</span><span className="forgot">忘れ</span><span className="missed">飲み忘れ</span>
          </div>

          <section className="pill-panel" aria-live="polite">
            <h2>{selectedLabel || '今日'}</h2>
            <p>{actionMessage(selectedStatus, isTodaySelected ? data : null)}</p>
            {error && <div className="pill-alert">{error}</div>}
            {success && <div className="pill-success">{success}</div>}
            {isTodaySelected ? (
              <div className="pill-actions">
                {data?.status === 'pending' ? (
                  <>
                    <button className="pill-action taken" disabled={acting} onClick={() => act('taken')}>服用しました</button>
                    <button className="pill-action forgot" disabled={acting} onClick={() => act('forgot')}>忘れました</button>
                    <button className="pill-action missed" disabled={acting} onClick={() => act('missed')}>飲み忘れ</button>
                  </>
                ) : (
                  <button className="pill-action undo" disabled={acting} onClick={() => act('undo')}>今日の記録を取り消す</button>
                )}
              </div>
            ) : (
              <p>過去の日付は確認のみできます。</p>
            )}
          </section>
        </div>
      </main>
    </>
  );
}
