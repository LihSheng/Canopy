type Props = {
  nodes: { id: string; type: string; label: string }[];
  edges: { from: string; to: string; type: string }[];
};

export function LineageView({ nodes, edges }: Props) {
  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-zinc-500">
        No lineage data available
      </div>
    );
  }

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {nodes.map((node) => (
          <div
            key={node.id}
            className="rounded-lg border border-zinc-200 bg-white px-3 py-2 shadow-sm"
          >
            <span className="text-xs font-medium text-zinc-500">{node.type}</span>
            <p className="text-sm font-medium text-zinc-900">{node.label}</p>
          </div>
        ))}
      </div>
      {edges.length > 0 && (
        <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
            Edges
          </h4>
          <ul className="space-y-1">
            {edges.map((edge, i) => {
              const from = nodeMap.get(edge.from);
              const to = nodeMap.get(edge.to);
              return (
                <li key={i} className="text-sm text-zinc-700">
                  {from?.label || edge.from} → {to?.label || edge.to}
                  <span className="ml-2 text-xs text-zinc-400">({edge.type})</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
