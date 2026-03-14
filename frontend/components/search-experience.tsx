"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import {
  CompletedEvent,
  PlatformErrorEvent,
  PlatformResultsEvent,
  PlatformStatus,
  ProductGroup,
  StartedEvent,
} from "@/lib/types";

type SearchState = "idle" | "searching" | "completed" | "error";

const platformOrder = ["blinkit", "instamart"];

const titleCase = (value: string): string =>
  value.length > 0 ? `${value[0].toUpperCase()}${value.slice(1)}` : value;

export function SearchExperience() {
  const eventSourceRef = useRef<EventSource | null>(null);
  const [item, setItem] = useState("");
  const [pincode, setPincode] = useState("");
  const [groups, setGroups] = useState<ProductGroup[]>([]);
  const [state, setState] = useState<SearchState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [platformStatus, setPlatformStatus] = useState<Record<string, PlatformStatus>>(
    {},
  );
  const [activeSearch, setActiveSearch] = useState<{ item: string; pincode: string } | null>(
    null,
  );

  const sortedGroups = useMemo(
    () =>
      groups
        .map((group) => ({
          ...group,
          offers: [...group.offers].sort((a, b) => a.price - b.price),
        }))
        .sort((a, b) => a.canonical_name.localeCompare(b.canonical_name)),
    [groups],
  );

  const statusEntries = useMemo(() => {
    const allKeys = new Set<string>([
      ...platformOrder,
      ...Object.keys(platformStatus),
      ...sortedGroups.flatMap((group) => group.offers.map((offer) => offer.platform.toLowerCase())),
    ]);
    const entries: Array<[string, PlatformStatus]> = Array.from(allKeys).map((platform) => [
      platform,
      platformStatus[platform] ?? "pending",
    ]);
    return entries;
  }, [platformStatus, sortedGroups]);

  const runSearch = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();

    const normalizedItem = item.trim();
    const normalizedPincode = pincode.trim();

    if (!normalizedItem || !normalizedPincode) {
      setErrorMessage("Please enter both product and pincode.");
      return;
    }

    setErrorMessage(null);
    setState("searching");
    setGroups([]);
    setActiveSearch({ item: normalizedItem, pincode: normalizedPincode });

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    const params = new URLSearchParams({ item: normalizedItem, pincode: normalizedPincode });
    const source = new EventSource(`/api/search?${params.toString()}`);
    eventSourceRef.current = source;

    source.addEventListener("started", (rawEvent) => {
      const started = JSON.parse((rawEvent as MessageEvent).data) as StartedEvent;
      setPlatformStatus(
        Object.fromEntries(started.platforms.map((platform) => [platform.toLowerCase(), "pending"])),
      );
    });

    source.addEventListener("platform_results", (rawEvent) => {
      const payload = JSON.parse((rawEvent as MessageEvent).data) as PlatformResultsEvent;
      const normalizedPlatform = payload.platform.toLowerCase();
      setPlatformStatus((prev) => ({ ...prev, [normalizedPlatform]: "success" }));
      setGroups(payload.groups);
    });

    source.addEventListener("platform_error", (rawEvent) => {
      const payload = JSON.parse((rawEvent as MessageEvent).data) as PlatformErrorEvent;
      const normalizedPlatform = payload.platform.toLowerCase();
      setPlatformStatus((prev) => ({ ...prev, [normalizedPlatform]: "error" }));
    });

    source.addEventListener("completed", (rawEvent) => {
      const payload = JSON.parse((rawEvent as MessageEvent).data) as CompletedEvent;
      const normalizedStatus = Object.fromEntries(
        Object.entries(payload.status).map(([platform, status]) => [platform.toLowerCase(), status]),
      ) as Record<string, PlatformStatus>;

      setPlatformStatus(normalizedStatus);
      setGroups(payload.groups);
      setState("completed");
      source.close();
      if (eventSourceRef.current === source) {
        eventSourceRef.current = null;
      }
    });

    source.onerror = () => {
      setState("error");
      setErrorMessage("Search stream disconnected. Please try again.");
      source.close();
      if (eventSourceRef.current === source) {
        eventSourceRef.current = null;
      }
    };
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <main className="shell">
      <nav className="top-nav" aria-label="Primary">
        <div className="nav-left" aria-hidden="true">
          <span className="diamond-icon" />
        </div>
        <p className="brand-mark">Grocery Compare</p>
        <div className="nav-meta" aria-hidden="true">
          <span className="utility-icon" />
          <span className="utility-icon cart" />
        </div>
      </nav>

      <section className="hero">
        <header className="hero-header">
          <span className="hero-emblem" aria-hidden="true" />
          <span className="eyebrow">Live Grocery Intelligence</span>
          <h1>Find the best grocery deal as each platform finishes scraping.</h1>
          <p>
            Enter a product and pincode to stream Blinkit and Instamart pricing in real time.
            Product cards appear progressively so you do not wait for all providers.
          </p>
        </header>

        <div className="search-rail">
          <form className="search-panel" onSubmit={runSearch}>
            <div className="search-field">
              <label htmlFor="item">Product search</label>
              <input
                id="item"
                type="text"
                value={item}
                onChange={(event) => setItem(event.target.value)}
                placeholder="milk"
                required
              />
            </div>

            <div className="search-field">
              <label htmlFor="pincode">Pincode</label>
              <input
                id="pincode"
                type="text"
                inputMode="numeric"
                value={pincode}
                onChange={(event) => setPincode(event.target.value.replace(/[^0-9]/g, ""))}
                placeholder="411001"
                maxLength={12}
                required
              />
            </div>

            <button type="submit" disabled={state === "searching"}>
              {state === "searching" ? "Streaming Results..." : "Start Comparison"}
            </button>
          </form>
        </div>

        {(activeSearch || errorMessage) && (
          <div className="meta-strip" role="status" aria-live="polite">
            {activeSearch ? (
              <p>
                Query: <strong>{activeSearch.item}</strong> in <strong>{activeSearch.pincode}</strong>
              </p>
            ) : null}
            {errorMessage ? <p className="error-text">{errorMessage}</p> : null}
          </div>
        )}
      </section>

      <section className="results-wrapper" aria-live="polite">
        <div className="section-heading">
          <h2>Streaming Results</h2>
          <p>Each platform updates independently and cards refresh as new offers are found.</p>
        </div>

        <div className="platform-grid">
          {statusEntries.map(([platform, status]) => (
            <article key={platform} className={`platform-chip status-${status}`}>
              <h3>{titleCase(platform)}</h3>
              <p>
                {status === "pending" && "Waiting"}
                {status === "success" && "Offers received"}
                {status === "done" && "Completed"}
                {status === "error" && "Unavailable"}
              </p>
            </article>
          ))}
        </div>

        {sortedGroups.length === 0 ? (
          <article className="empty-card">
            <h2>{state === "searching" ? "Listening for platform updates..." : "No results yet"}</h2>
            <p>
              Enter a product and pincode to start. Product cards will appear progressively as each
              platform returns data.
            </p>
          </article>
        ) : (
          <div className="group-grid">
            {sortedGroups.map((group) => (
              <article className="group-card" key={group.group_id}>
                <header>
                  <h2>{group.canonical_name}</h2>
                  {group.cheapest_offer ? (
                    <p className="cheapest-note">
                      Best price: {titleCase(group.cheapest_offer.platform)} - INR {group.cheapest_offer.price}
                    </p>
                  ) : null}
                </header>

                <div className="offer-stack">
                  {group.offers.map((offer, index) => {
                    const isCheapest =
                      group.cheapest_offer?.platform === offer.platform &&
                      group.cheapest_offer?.name === offer.name;

                    return (
                      <a
                        key={`${offer.platform}-${offer.name}-${index}`}
                        href={offer.url}
                        target="_blank"
                        rel="noreferrer"
                        className={`offer-row ${isCheapest ? "cheapest" : ""}`}
                      >
                        <div>
                          <h3>{titleCase(offer.platform)}</h3>
                          <p>{offer.name}</p>
                        </div>
                        <strong>INR {offer.price}</strong>
                      </a>
                    );
                  })}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
