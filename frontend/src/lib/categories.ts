import type { Category, ItemType } from "../types";

export interface CategoryStyle {
  label: string;
  img: string; // our own illustration in public/img
  alt: string;
  chip: string; // tinted background + dark text (AA)
  bar: string; // solid accent for timeline markers
  border: string;
}

export const CATEGORY: Record<Category, CategoryStyle> = {
  food: { label: "Food", img: "/img/food.svg", alt: "Food illustration", chip: "bg-clay-100 text-clay-700", bar: "bg-clay-500", border: "border-l-clay-500" },
  music: { label: "Music", img: "/img/music.svg", alt: "Music illustration", chip: "bg-teal-100 text-teal-800", bar: "bg-teal-700", border: "border-l-teal-700" },
  social: { label: "People", img: "/img/social.svg", alt: "People meeting illustration", chip: "bg-olive-100 text-olive-700", bar: "bg-olive-700", border: "border-l-olive-700" },
  venue: { label: "Places", img: "/img/venue.svg", alt: "Storefront illustration", chip: "bg-plum-100 text-plum-700", bar: "bg-plum-700", border: "border-l-plum-700" },
  activity: { label: "Things to do", img: "/img/activity.svg", alt: "Festival illustration", chip: "bg-slate-100 text-slate-700", bar: "bg-slate-700", border: "border-l-slate-700" },
};

export const categoryStyle = (c: string): CategoryStyle => CATEGORY[c as Category] ?? CATEGORY.activity;

/** Mirrors backend resolver.SEARCH_TYPE: which Qloo search type each loved-item type is looked up as. */
export const SEARCH_AS: Record<ItemType, string> = {
  dish: "place",
  artist: "artist",
  show: "TV show",
  place: "place",
  activity: "any type",
};
