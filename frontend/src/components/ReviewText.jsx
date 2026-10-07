// 지원하는 서식만 React 텍스트로 표시합니다. 모델 출력의 HTML은 실행하지 않습니다.
export default function ReviewText({ text }) {
  return <div className="space-y-2">{String(text || '').split('\n').map((line, index) => {
    if (!line.trim()) return null;
    if (/^---+$/.test(line.trim())) return <hr key={index} className="border-slate-700" />;
    const heading = /^#{1,6}\s/.test(line);
    const content = line.replace(/^#{1,6}\s+/, '').replace(/^\s*[*-]\s+/, '• ');
    const parts = content.split(/(\*\*.*?\*\*)/g).map((part, i) => part.startsWith('**') && part.endsWith('**')
      ? <strong key={i} className="font-semibold text-slate-100">{part.slice(2, -2)}</strong> : part);
    return heading ? <h5 key={index} className="pt-3 font-bold text-amber-200">{parts}</h5> : <p key={index}>{parts}</p>;
  })}</div>;
}
