"use client";

import { useCallback, useEffect, useState } from "react";
import { CategoryFilter } from "@/components/CategoryFilter";
import { ProductCard } from "@/components/ProductCard";
import { fetchProducts, type Product } from "@/lib/api";

const PAGE_SIZE = 24;

export default function HomePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [category, setCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const loadInitial = useCallback(async (cat: string | null) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProducts({ limit: PAGE_SIZE, category: cat });
      setProducts(data.products);
      setCursor(data.next_cursor);
      setHasMore(data.has_more);
      setTotal(data.products.length);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load products");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitial(category);
  }, [category, loadInitial]);

  const handleCategoryChange = (cat: string | null) => {
    setCategory(cat);
  };

  const handleLoadMore = async () => {
    if (!cursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const data = await fetchProducts({
        limit: PAGE_SIZE,
        category,
        cursor,
      });
      setProducts((prev) => [...prev, ...data.products]);
      setCursor(data.next_cursor);
      setHasMore(data.has_more);
      setTotal((prev) => prev + data.products.length);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load more");
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas">
      {/* Header */}
      <header className="border-b border-border sticky top-0 z-10 bg-canvas/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center text-white font-bold text-sm">
              CV
            </div>
            <span className="font-semibold text-gray-100 tracking-tight">
              CodeVector
            </span>
          </div>
          <span className="text-xs text-muted font-mono">
            Cursor-based pagination
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-semibold text-gray-100">Products</h1>
            {!loading && (
              <span className="text-sm text-muted font-mono">
                {total} shown
              </span>
            )}
          </div>
          <CategoryFilter selected={category} onChange={handleCategoryChange} />
        </section>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: PAGE_SIZE }).map((_, i) => (
              <div
                key={i}
                className="bg-surface border border-border rounded-xl p-5 h-28 animate-pulse"
              />
            ))}
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-20 text-muted">
            <p className="text-lg mb-2">No products found</p>
            <p className="text-sm">
              {category
                ? `No products in "${category}" category.`
                : "The database appears to be empty. Run the seed script to populate it."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}

        {/* Load more */}
        {hasMore && !loading && (
          <div className="mt-10 flex justify-center">
            <button
              onClick={handleLoadMore}
              disabled={loadingMore}
              className="px-8 py-3 rounded-xl bg-surface border border-border text-sm font-medium text-gray-300 hover:border-accent hover:text-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-mono"
            >
              {loadingMore ? (
                <span className="flex items-center gap-2">
                  <svg
                    className="animate-spin h-4 w-4"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v8H4z"
                    />
                  </svg>
                  Loading…
                </span>
              ) : (
                "Load more"
              )}
            </button>
          </div>
        )}

        {!hasMore && products.length > 0 && !loading && (
          <p className="mt-10 text-center text-xs text-muted font-mono">
            — end of results ({total} products) —
          </p>
        )}
      </main>
    </div>
  );
}
