import { useState } from 'react';
const names = ['T1', 'Gen.G', 'Hanwha Life Esports', 'KT Rolster', 'Dplus KIA', 'BNK FEARX', 'DN SOOPers', 'Nongshim RedForce', 'KIWOOM DRX', 'HANJIN BRION'];
export default function TeamLogo({ team, className = 'h-8 w-8' }) {
  const [failedFor, setFailedFor] = useState(null);
  const filename = names.find(name => name.toLowerCase() === team?.toLowerCase());
  const src = filename && failedFor !== team ? `/teams/${encodeURIComponent(filename)}.png` : '/team-placeholder.svg';
  return <img src={src} alt="" aria-hidden="true" onError={() => setFailedFor(team)} className={`${className} shrink-0 rounded bg-white/90 p-1 object-contain`} />;
}
