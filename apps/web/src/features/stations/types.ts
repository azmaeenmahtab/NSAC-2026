export type ThreatLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

export interface ThreatSummary {
  level: ThreatLevel;
  headline: string;
  explanation: string;
  nearby_recent_events: number;
}

export interface NearbyStationItem {
  station_id: string;
  name: string;
  district_id: string;
  district_name: string;
  lat: number;
  lon: number;
  distance_km: number;
  hotline: string;
  national_emergency: string;
  phone?: string | null;
  email?: string | null;
  dial_number: string;
  email_subject: string;
  email_body: string;
}

export interface NearbyStationsData {
  center_lat: number;
  center_lon: number;
  location_source: string;
  area_id: string;
  area_name: string;
  threat: ThreatSummary;
  stations: NearbyStationItem[];
}

