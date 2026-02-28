import { useRef, useCallback, useEffect, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { SECTOR_COLORS, EDGE_COLORS, EDGE_LABELS } from '../../utils/colors';

const EDGE_DESCRIPTIONS = {
  COMPETES_WITH:          'Both companies target the same buyers with similar products. Thicker line = stronger competitive overlap.',
  DISRUPTS:               "One company's approach actively threatens another's core market position.",
  PARTNERS_WITH:          'A documented integration, reseller, or technology partnership exists between the two.',
  TARGETS_SAME_SEGMENT:   'Both companies sell into the same buyer segment (e.g. Cloud Data Platforms).',
  SHARES_INVESTMENT_THEME:'Both companies benefit from the same macro investment narrative (e.g. open source, consumption pricing).',
  SUPPLIES_TO:            "One company's product is a key input or dependency for the other.",
};

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export default function GraphPanel({ graphData, height = 500, onNodeClick }) {
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
        onNodeClick={(node) => {
          if (onNodeClick && node.label) onNodeClick(node.label);
        }}
        nodeLabel={(node) => onNodeClick ? `Search: Competitors to ${node.label}` : node.label}
        linkColor={(link) => link.color}
        linkWidth={(link) => Math.max(0.5, (link.strength || 0.5) * 2)}
        linkDirectionalParticles={0}
        cooldownTicks={150}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.25}
      />

      {/* How to read this graph */}
      <div className="px-4 py-3 border-t border-surface-200 bg-surface-50 text-xs text-surface-600">
        <p className="font-semibold text-surface-800 mb-2">How to read this graph</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Nodes */}
          <div>
            <p className="font-medium text-surface-700 mb-1.5">Nodes (companies)</p>
            <ul className="space-y-1 leading-relaxed">
              <li><span className="font-medium text-surface-800">Glow</span> — the query company (your starting point)</li>
              <li><span className="font-medium text-surface-800">Size</span> — proportional to market cap; larger = bigger company</li>
              <li><span className="font-medium text-surface-800">Colour</span> — sector (see legend above)</li>
              {onNodeClick && (
                <li><span className="font-medium text-surface-800">Click</span> — runs "Competitors to …" search for that company</li>
              )}
            </ul>
          </div>

          {/* Edges */}
          <div>
            <p className="font-medium text-surface-700 mb-1.5">Edges (relationships)</p>
            <ul className="space-y-1 leading-relaxed">
              {Object.entries(EDGE_DESCRIPTIONS).map(([type, desc]) => (
                <li key={type} className="flex gap-2">
                  <span
                    className="mt-0.5 shrink-0 inline-block w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: EDGE_COLORS[type] }}
                  />
                  <span>
                    <span className="font-medium text-surface-800">{EDGE_LABELS[type]}</span>
                    {' — '}
                    {desc}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <p className="mt-2.5 text-surface-500 italic">
          Line thickness reflects relationship strength — thicker lines indicate a stronger or more documented connection.
        </p>
      </div>
    </div>
  );
}
