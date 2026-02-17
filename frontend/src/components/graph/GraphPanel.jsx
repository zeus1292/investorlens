import { useRef, useCallback, useEffect, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { SECTOR_COLORS, EDGE_COLORS } from '../../utils/colors';

export default function GraphPanel({ graphData, height = 350 }) {
  const fgRef = useRef();

  const data = useMemo(() => {
    if (!graphData || !graphData.nodes?.length) return { nodes: [], links: [] };

    const nodes = graphData.nodes.map((n) => ({
      ...n,
      color: SECTOR_COLORS[n.sector] || '#6b7280',
      val: Math.max(4, Math.min(20, (n.market_cap_b || 5) * 0.5)),
    }));

    // Deduplicate edges (bidirectional)
    const seen = new Set();
    const links = [];
    for (const e of graphData.edges || []) {
      if (!e.source || !e.target || e.source === e.target) continue;
      const key = [e.source, e.target].sort().join('|') + '|' + e.type;
      if (seen.has(key)) continue;
      seen.add(key);
      links.push({
        source: e.source,
        target: e.target,
        type: e.type,
        strength: e.strength || 0.5,
        color: EDGE_COLORS[e.type] || '#4b5563',
      });
    }

    return { nodes, links };
  }, [graphData]);

  // Zoom to fit on data change
  useEffect(() => {
    if (fgRef.current && data.nodes.length > 0) {
      setTimeout(() => fgRef.current.zoomToFit(400, 40), 300);
    }
  }, [data]);

  const paintNode = useCallback((node, ctx) => {
    const size = node.val || 6;

    // Glow for center node
    if (node.is_center) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI);
      ctx.fillStyle = `${node.color}30`;
      ctx.fill();
    }

    // Node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = node.color;
    ctx.fill();

    if (node.is_center) {
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Label
    ctx.font = `${node.is_center ? 'bold ' : ''}10px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = '#d1d5db';
    ctx.fillText(node.label, node.x, node.y + size + 3);
  }, []);

  if (!data.nodes.length) return null;

  return (
    <div className="rounded-xl bg-surface-800 border border-surface-700 overflow-hidden">
      <div className="px-3 py-2 border-b border-surface-700">
        <span className="text-xs font-medium text-surface-400">Relationship Graph</span>
      </div>
      <ForceGraph2D
        ref={fgRef}
        graphData={data}
        width={undefined}
        height={height}
        backgroundColor="#1f2937"
        nodeCanvasObject={paintNode}
        nodePointerAreaPaint={(node, color, ctx) => {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.val + 4, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        linkColor={(link) => link.color}
        linkWidth={(link) => Math.max(1, (link.strength || 0.5) * 3)}
        linkDirectionalParticles={0}
        cooldownTicks={80}
        d3AlphaDecay={0.04}
        d3VelocityDecay={0.3}
      />
    </div>
  );
}
