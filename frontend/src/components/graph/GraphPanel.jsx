import { useRef, useCallback, useEffect, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { SECTOR_COLORS, EDGE_COLORS } from '../../utils/colors';

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export default function GraphPanel({ graphData, height = 500 }) {
  const fgRef = useRef();

  const data = useMemo(() => {
    if (!graphData || !graphData.nodes?.length) return { nodes: [], links: [] };

    const nodes = graphData.nodes.map((n) => ({
      ...n,
      color: SECTOR_COLORS[n.sector] || '#6b7280',
      // Keep nodes small — 3px to 7px radius
      val: n.is_center ? 7 : Math.max(3, Math.min(6, (n.market_cap_b || 5) * 0.12)),
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

  // Configure forces for a spread-out layout + zoom to fit
  useEffect(() => {
    if (!fgRef.current || data.nodes.length === 0) return;

    const fg = fgRef.current;

    // Strong repulsion to push nodes far apart
    fg.d3Force('charge').strength(-300).distanceMax(400);

    // Long link distance so connected nodes don't huddle
    fg.d3Force('link').distance(100);

    // Gentle centering
    fg.d3Force('center').strength(0.05);

    // Reheat the simulation so new forces take effect
    fg.d3ReheatSimulation();

    // Zoom to fit after it settles
    setTimeout(() => fg.zoomToFit(400, 60), 800);
  }, [data]);

  const paintNode = useCallback((node, ctx) => {
    const size = node.val || 4;
    const isCtr = node.is_center;
    const nodeAlpha = isCtr ? 0.9 : 0.55;

    // Glow for center node
    if (isCtr) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI);
      ctx.fillStyle = hexToRgba(node.color, 0.15);
      ctx.fill();
    }

    // Node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = hexToRgba(node.color, nodeAlpha);
    ctx.fill();

    // Colored stroke
    ctx.strokeStyle = hexToRgba(node.color, Math.min(nodeAlpha + 0.3, 1));
    ctx.lineWidth = isCtr ? 2 : 1;
    ctx.stroke();

    // Label with background pill for readability
    const fontSize = isCtr ? 11 : 9;
    ctx.font = `${isCtr ? 'bold ' : ''}${fontSize}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    const labelY = node.y + size + 3;
    const textWidth = ctx.measureText(node.label).width;

    ctx.fillStyle = 'rgba(244, 248, 245, 0.85)';
    ctx.fillRect(node.x - textWidth / 2 - 2, labelY - 1, textWidth + 4, fontSize + 3);

    ctx.fillStyle = '#1a2e24';
    ctx.fillText(node.label, node.x, labelY);
  }, []);

  if (!data.nodes.length) return null;

  return (
    <div className="rounded-xl bg-white border border-surface-200 overflow-hidden shadow-sm">
      <div className="px-3 py-2 border-b border-surface-200 flex items-center justify-between">
        <span className="text-xs font-medium text-surface-600">Relationship Graph</span>
        <div className="flex gap-3">
          {Object.entries(SECTOR_COLORS).map(([sector, color]) => (
            <span key={sector} className="flex items-center gap-1 text-[9px] text-surface-500">
              <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
              {sector.split('/')[0]}
            </span>
          ))}
        </div>
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
          ctx.arc(node.x, node.y, node.val + 6, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        linkColor={(link) => link.color}
        linkWidth={(link) => Math.max(0.5, (link.strength || 0.5) * 2)}
        linkDirectionalParticles={0}
        cooldownTicks={150}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.25}
      />
    </div>
  );
}
