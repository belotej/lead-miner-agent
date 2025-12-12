interface StatusBadgeProps {
  status: string;
}

const statusStyles: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700',
  contacted: 'bg-yellow-100 text-yellow-700',
  qualified: 'bg-green-100 text-green-700',
  proposal: 'bg-purple-100 text-purple-700',
  won: 'bg-emerald-100 text-emerald-700',
  lost: 'bg-red-100 text-red-700',
  archived: 'bg-slate-100 text-slate-700',
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const style = statusStyles[status] || statusStyles.new;
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${style}`}>
      {status}
    </span>
  );
}
