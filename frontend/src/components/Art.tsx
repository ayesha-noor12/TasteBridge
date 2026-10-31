import { useState } from "react";
import { categoryStyle } from "../lib/categories";
import { Icon, type IconName } from "./Icon";

/**
 * Our own SVG illustration for a category. If the file fails to load, the tinted box and icon
 * underneath stay visible, so the layout never breaks.
 */
export function Illustration({ src, alt, icon, tint, className = "", eager = false }: { src: string; alt: string; icon: IconName; tint: string; className?: string; eager?: boolean }) {
  const [ok, setOk] = useState(true);
  return (
    <div className={`relative grid place-items-center overflow-hidden ${tint} ${className}`}>
      <Icon name={icon} className="h-7 w-7 opacity-60" />
      {ok && (
        <img
          src={src}
          alt={alt}
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          className="absolute inset-0 h-full w-full object-cover"
          onError={() => setOk(false)}
        />
      )}
    </div>
  );
}

/**
 * Qloo's own photo for a place (food or venue); our illustration otherwise. Artist photos are never
 * shown, because they depict real, identifiable people.
 */
export function Thumb({ category, photo, name, className = "" }: { category: string; photo?: string | null; name?: string; className?: string }) {
  const s = categoryStyle(category);
  const icon = (["food", "music", "social", "venue", "activity"].includes(category) ? category : "activity") as IconName;
  const usePhoto = photo && photo.startsWith("https://images.qloo.com/") && (category === "food" || category === "venue");
  return usePhoto ? (
    <Illustration src={photo} alt={`Photo of ${name ?? "this place"} (via Qloo)`} icon={icon} tint={s.chip} className={`rounded-2xl ${className}`} />
  ) : (
    <Illustration src={s.img} alt={s.alt} icon={icon} tint={s.chip} className={`rounded-2xl ${className}`} />
  );
}
