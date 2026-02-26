import { useState } from 'react';
import { getCompanyDomain } from '../../utils/logos';

/**
 * Displays a company logo using Google's favicon service.
 * Falls back to a grey initials avatar if no domain is mapped or the image fails.
 *
 * Props:
 *   companyId  — company_id string (preferred, most reliable lookup)
 *   name       — display name (used for initials fallback + alt text)
 *   size       — pixel dimension for width + height (default 28)
 *   className  — extra Tailwind classes on the wrapper
 */
export default function CompanyLogo({ companyId, name, size = 28, className = '' }) {
  const [failed, setFailed] = useState(false);
  const domain = getCompanyDomain(companyId) ?? getCompanyDomain(name);

  const initials = (name || '?')
    .split(/[\s\.]+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('');

  const shared = `shrink-0 rounded-md overflow-hidden ${className}`;

  if (!domain || failed) {
    return (
      <div
        className={`${shared} bg-surface-100 flex items-center justify-center text-surface-500 font-semibold`}
        style={{ width: size, height: size, fontSize: size * 0.36 }}
        title={name}
      >
        {initials}
      </div>
    );
  }

  // Google's favicon service: reliable, free, no API key, up to 128px
  const src = `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;

  return (
    <img
      src={src}
      alt={`${name} logo`}
      width={size}
      height={size}
      className={`${shared} object-contain bg-white p-0.5`}
      onError={() => setFailed(true)}
      title={name}
    />
  );
}
