import clsx from "clsx";

export function StreamingCursor() {
  return (
    <span 
      className={clsx(
        "inline-block w-1.5 h-4 ml-1 bg-primary align-middle",
        "animate-[pulse-glow_1s_ease-in-out_infinite]"
      )}
    />
  );
}
