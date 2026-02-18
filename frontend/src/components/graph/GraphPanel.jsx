import { useRef, useCallback, useEffect, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { SECTOR_COLORS, EDGE_COLORS } from '../../utils/colors';

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

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
    const isCtr = node.is_center;
    const nodeAlpha = isCtr ? 0.85 : 0.4;

    // Glow for center node
    if (isCtr) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 5, 0, 2 * Math.PI);
      ctx.fillStyle = hexToRgba(node.color, 0.15);
      ctx.fill();
    }

    // Node circle — reduced opacity for non-center
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = hexToRgba(node.color, nodeAlpha);
    ctx.fill();

    // Stroke to distinguish colors
    ctx.strokeStyle = hexToRgba(node.color, Math.min(nodeAlpha + 0.3, 1));
    ctx.lineWidth = isCtr ? 2.5 : 1.5;
    ctx.stroke();

    // Label — prominent, with subtle background for readability
    const fontSize = isCtr ? 11 : 10;
    ctx.font = `${isCtr ? 'bold ' : ''}${fontSize}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    const labelY = node.y + size + 4;
    const textWidth = ctx.measureText(node.label).width;
    ctx.fillStyle = 'rgba(244, 248, 245, 0.8)';
    ctx.fillRect(node.x - textWidth / 2 - 2, labelY - 1, textWidth + 4, fontSize + 2);

    ctx.fillStyle = '#1a2e24';
    ctx.fillText(node.label, node.x, labelY);
  }, []);

  if (!data.nodes.length) return null;

  return (
    <div className="rounded-xl bg-white border border-surface-200 overflow-hidden shadow-sm">
      <div className="px-3 py-2 border-b border-surface-200">
        <span className="text-xs font-medium text-surface-600">Relationship Graph</span>
      </div>
      <ForceGraph2D
        ref={fgRef}
        graphData={data}
        width={undefined}
        height={height}
        backgroundColor="#f0f4f2"
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
