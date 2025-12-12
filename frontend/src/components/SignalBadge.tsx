interface SignalBadgeProps {
  strength: string;
}

const strengthStyles: Record<string, string> = {
  'Very High': 'bg-emerald-100 text-emerald-700 border-emerald-200',
  'High': 'bg-green-100 text-green-700 border-green-200',
  'Medium': 'bg-yellow-100 text-yellow-700 border-yellow-200',
  'Low': 'bg-slate-100 text-slate-600 border-slate-200',
};

export function SignalBadge({ strength }: SignalBadgeProps) {
  const style = strengthStyles[strength] || strengthStyles.Medium;
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${style}`}>
      {strength}
    </span>
  );
}
