import type { Product } from "@/lib/api";

interface Props {
  product: Product;
}

const CATEGORY_COLORS: Record<string, string> = {
  Electronics: "text-blue-400 bg-blue-400/10",
  Books: "text-amber-400 bg-amber-400/10",
  Clothing: "text-pink-400 bg-pink-400/10",
  "Home & Garden": "text-green-400 bg-green-400/10",
  "Sports & Outdoors": "text-orange-400 bg-orange-400/10",
  "Toys & Games": "text-purple-400 bg-purple-400/10",
  "Food & Grocery": "text-lime-400 bg-lime-400/10",
  "Beauty & Personal Care": "text-rose-400 bg-rose-400/10",
  Automotive: "text-cyan-400 bg-cyan-400/10",
  "Health & Wellness": "text-teal-400 bg-teal-400/10",
};

function formatPrice(price: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number(price));
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function ProductCard({ product }: Props) {
  const colorClass =
    CATEGORY_COLORS[product.category] ?? "text-gray-400 bg-gray-400/10";

  return (
    <div className="bg-surface border border-border rounded-xl p-5 flex flex-col gap-3 hover:border-accent/50 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-medium text-gray-100 leading-snug line-clamp-2">
          {product.name}
        </h3>
        <span className="text-base font-semibold text-accent whitespace-nowrap font-mono">
          {formatPrice(product.price)}
        </span>
      </div>

      <div className="flex items-center justify-between mt-auto">
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}
        >
          {product.category}
        </span>
        <span className="text-xs text-muted font-mono">
          {formatDate(product.created_at)}
        </span>
      </div>
    </div>
  );
}
