import React from "react";

export default function AccentLines() {
  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Horizontal lines */}
      <div className="absolute h-px left-0 right-0 bg-border/75 opacity-75 top-[20%] animate-draw-x animate-delay-150ms"></div>
      <div className="absolute h-px left-0 right-0 bg-border/75 opacity-75 top-[50%] animate-draw-x animate-delay-280ms"></div>
      <div className="absolute h-px left-0 right-0 bg-border/75 opacity-75 top-[80%] animate-draw-x animate-delay-410ms"></div>
      
      {/* Vertical lines */}
      <div className="absolute w-px top-0 bottom-0 bg-border/75 opacity-75 left-[20%] animate-draw-y animate-delay-520ms"></div>
      <div className="absolute w-px top-0 bottom-0 bg-border/75 opacity-75 left-[50%] animate-draw-y animate-delay-640ms"></div>
      <div className="absolute w-px top-0 bottom-0 bg-border/75 opacity-75 left-[80%] animate-draw-y animate-delay-760ms"></div>
    </div>
  );
}
