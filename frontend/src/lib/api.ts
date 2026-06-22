const API_BASE =
  typeof window !== "undefined"
    ? "/api"
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

export interface Product {
  id: number;
  name: string;
  category: string;
  price: string;
  created_at: string;
  updated_at: string;
}

export interface ProductListResponse {
  products: Product[];
  next_cursor: string | null;
  has_more: boolean;
}

export async function fetchProducts(params: {
  limit?: number;
  category?: string | null;
  cursor?: string | null;
}): Promise<ProductListResponse> {
  const url =
  typeof window !== "undefined"
    ? new URL(`${API_BASE}/products`, window.location.origin)
    : new URL(`${API_BASE}/products`);

  if (params.limit) url.searchParams.set("limit", String(params.limit));
  if (params.category) url.searchParams.set("category", params.category);
  if (params.cursor) url.searchParams.set("cursor", params.cursor);

  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<ProductListResponse>;
}

export async function fetchCategories(): Promise<string[]> {
  // The API doesn't have a /categories endpoint, so we infer from the
  // first page of products. For production, add a dedicated endpoint.
  const data = await fetchProducts({ limit: 100 });
  const cats = Array.from(new Set(data.products.map((p) => p.category))).sort();
  return cats;
}
