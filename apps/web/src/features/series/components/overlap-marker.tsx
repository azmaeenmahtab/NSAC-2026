import * as React from "react";
import { ReferenceLine } from "recharts";

export interface OverlapMarkerProps {
  x?: string; // date key e.g. "2012-02"
}

export function OverlapMarker({ x = "2012-02" }: OverlapMarkerProps) {
  return (
    <ReferenceLine
      x={x}
      stroke="#a855f7"
      strokeDasharray="4 4"
      strokeWidth={1.5}
      label={{
        value: "VIIRS S-NPP Era Begins (2012-02)",
        position: "top",
        fill: "#a855f7",
        fontSize: 10,
        fontWeight: 600,
      }}
    />
  );
}
