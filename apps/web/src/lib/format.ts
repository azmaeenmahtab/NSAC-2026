const FULL_MONTH_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const SHORT_MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

export function formatMonthFull(month: number | string): string {
  const m = typeof month === "string" ? parseInt(month, 10) : month;
  if (isNaN(m) || m < 1 || m > 12) return String(month);
  return FULL_MONTH_NAMES[m - 1];
}

export function formatMonthShort(month: number | string): string {
  const m = typeof month === "string" ? parseInt(month, 10) : month;
  if (isNaN(m) || m < 1 || m > 12) return String(month);
  return SHORT_MONTH_NAMES[m - 1];
}

export function formatNumber(
  value: number | null | undefined,
  decimals: number = 0
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "—";
  }
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatYearMonth(
  year: number | string,
  month: number | string
): string {
  const m = typeof month === "string" ? parseInt(month, 10) : month;
  const name = formatMonthFull(m);
  return `${name} ${year}`;
}

export function formatPercentile(rank: number | null | undefined): string {
  if (rank === null || rank === undefined || isNaN(rank)) {
    return "—";
  }
  const pct = rank <= 1.0 ? rank * 100 : rank;
  const rounded = Math.round(pct);
  const remainder10 = rounded % 10;
  const remainder100 = rounded % 100;

  let suffix = "th";
  if (remainder10 === 1 && remainder100 !== 11) suffix = "st";
  else if (remainder10 === 2 && remainder100 !== 12) suffix = "nd";
  else if (remainder10 === 3 && remainder100 !== 13) suffix = "rd";

  return `${rounded}${suffix}`;
}

export function formatFrp(frp: number | null | undefined): string {
  if (frp === null || frp === undefined || isNaN(frp)) {
    return "—";
  }
  return `${Math.round(frp)} MW`;
}

