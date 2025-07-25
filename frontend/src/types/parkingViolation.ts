// frontend/src/types/parkingViolation.ts

export type ViolationStatus = 'Ongoing' | 'Completed' | 'Acknowledged';

export interface ParkingViolationEvent {
  id: number;
  status: ViolationStatus;
  timestamp: string; // ISO 8601 format
  branch: {
    id: string;
    name: string;
  };
  camera: {
    id:string;
  };
  vehicleId: string;
  entryTime: string; // ISO 8601 format
  exitTime: string | null;
  durationMinutes: number;
  isViolation: boolean;
  total_parking_sessions: number;
  evidenceImageUrl?: string;
}

export interface ParkingKpiData {
  totalViolations: number;
  total_parking_sessions: number;
  ongoingViolations: number;
  avgViolationDuration: number; // in minutes
  avgNormalParkingTime: number; // in minutes
}