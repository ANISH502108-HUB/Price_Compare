export type PlatformStatus = "pending" | "success" | "error" | "done";

export type Product = {
  platform: string;
  name: string;
  price: number;
  url: string;
};

export type ProductGroup = {
  group_id: string;
  canonical_name: string;
  tokens: string[];
  offers: Product[];
  cheapest_offer: Product | null;
};

export type StartedEvent = {
  item: string;
  pincode: string;
  platforms: string[];
};

export type PlatformResultsEvent = {
  platform: string;
  products: Product[];
  groups: ProductGroup[];
  partial: boolean;
};

export type PlatformErrorEvent = {
  platform: string;
  error: string;
};

export type CompletedEvent = {
  item: string;
  pincode: string;
  status: Record<string, PlatformStatus>;
  groups: ProductGroup[];
  total_products: number;
};
