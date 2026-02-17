import CompetitorResults from './CompetitorResults';
import CompareResults from './CompareResults';
import AcquisitionResults from './AcquisitionResults';
import AttributeResults from './AttributeResults';
import { PERSONA_COLORS } from '../../utils/colors';

export default function ResultsContainer({ data }) {
  if (!data || !data.results) return null;

  const queryType = data.query?.query_type || 'competitors_to';
  const persona = data.persona || 'value_investor';
  const personaColor = PERSONA_COLORS[persona] || '#10b981';

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
        />
      );
  }
}
