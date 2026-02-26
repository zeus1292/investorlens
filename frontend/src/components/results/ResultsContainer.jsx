import CompetitorResults from './CompetitorResults';
import CompareResults from './CompareResults';
import AcquisitionResults from './AcquisitionResults';
import AttributeResults from './AttributeResults';
import { PERSONA_COLORS } from '../../utils/colors';

function PieChartInfo() {
  return (
    <div className="relative group inline-flex items-center gap-1.5 cursor-help select-none">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="w-4 h-4 text-gray-800 group-hover:text-black transition-colors"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="8" strokeLinecap="round" strokeWidth={2.5} />
        <line x1="12" y1="12" x2="12" y2="16" strokeLinecap="round" />
      </svg>
      <span className="text-xs font-medium text-gray-800 group-hover:text-black transition-colors">
        How to read scores
      </span>
      {/* Tooltip — drops below, right-aligned so it stays in viewport */}
      <div className="absolute top-full right-0 mt-2 w-80 bg-white text-gray-800 text-xs rounded-xl p-3.5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-30 shadow-xl border border-gray-200">
        {/* Arrow pointing up */}
        <div className="absolute bottom-full right-4 border-4 border-transparent border-b-gray-200" />
        <div className="absolute bottom-full right-[17px] border-[3px] border-transparent border-b-white" />
        <p className="font-semibold mb-2 text-black">Reading the score breakdown</p>
        <ul className="text-gray-600 leading-relaxed space-y-1 list-disc list-inside">
          <li>Click any card to expand its pie chart</li>
          <li>Each <span className="text-black font-medium">slice</span> = one scoring factor for this persona</li>
          <li>Bigger slice = higher weight in the ranking formula</li>
          <li>The <span className="text-black font-medium">number</span> next to each label is that factor&apos;s contribution out of 100 points</li>
          <li><span className="text-black font-medium">Graph Boost</span> is added for direct graph relationships (e.g. COMPETES_WITH strength)</li>
          <li>The <span className="text-black font-medium">overall score (0–1)</span> is the weighted sum of all factors</li>
        </ul>
      </div>
    </div>
  );
}

export default function ResultsContainer({ data }) {
  if (!data || !data.results) return null;

  const queryType = data.query?.query_type || 'competitors_to';
  const persona = data.persona || 'value_investor';
  const personaColor = PERSONA_COLORS[persona] || '#10b981';

  const inner = (() => {
    switch (queryType) {
      case 'compare':
        return (
          <CompareResults
            results={data.results}
            compareData={data.compare_data}
            personaColor={personaColor}
            query={data.query}
          />
        );
      case 'acquisition_target':
        return (
          <AcquisitionResults
            results={data.results}
            personaColor={personaColor}
            query={data.query}
          />
        );
      case 'attribute_search':
        return (
          <AttributeResults
            results={data.results}
            personaColor={personaColor}
            query={data.query}
          />
        );
      default:
        return (
          <CompetitorResults
            results={data.results}
            personaColor={personaColor}
            targetCompany={data.query?.target_company}
            targetCompanyId={data.query?.target_company}
          />
        );
    }
  })();

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <PieChartInfo />
      </div>
      {inner}
    </div>
  );
}
