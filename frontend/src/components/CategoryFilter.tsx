"use client";

const KNOWN_CATEGORIES = [
  "Electronics",
  "Books",
  "Clothing",
  "Home & Garden",
  "Sports & Outdoors",
  "Toys & Games",
  "Food & Grocery",
  "Beauty & Personal Care",
  "Automotive",
  "Health & Wellness",
];

interface Props {
  selected: string | null;
  onChange: (category: string | null) => void;
}

export function CategoryFilter({ selected, onChange }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onChange(null)}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
          selected === null
            ? "bg-accent text-white"
            : "bg-surface border border-border text-muted hover:border-accent hover:text-white"
        }`}
      >
        All
      </button>
      {KNOWN_CATEGORIES.map((cat) => (
        <button
          key={cat}
          onClick={() => onChange(cat === selected ? null : cat)}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            selected === cat
              ? "bg-accent text-white"
              : "bg-surface border border-border text-muted hover:border-accent hover:text-white"
          }`}
        >
          {cat}
        </button>
      ))}
    </div>
  );
}
