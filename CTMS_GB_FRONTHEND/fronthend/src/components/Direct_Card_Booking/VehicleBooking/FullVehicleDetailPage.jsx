import React, { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Car,
  MapPin,
  DollarSign,
  Route,
  Clock,
  Calendar,
  Package,
  Users,
  Navigation,
  CheckCircle,
  ArrowLeft,
  Phone,
  Shield,
  AlertCircle,
  CalendarDays,
  Timer,
  Loader2
} from "lucide-react";
import defaultVehicleImage from "../../../Home/GB_picture/Car.jpeg";

// Helper functions
const getPricingDisplay = (data) => {
  if (!data) {
    return {
      type: 'custom',
      primary: 'Contact for Price',
      secondary: '',
      icon: DollarSign,
      color: 'text-gray-600',
      description: 'Price available on request'
    };
  }

  if (data.is_long_drive) {
    if (data.per_day_rate) {
      return {
        type: 'daily',
        primary: `Rs. ${parseInt(data.per_day_rate).toLocaleString()}`,
        secondary: '/ day',
        icon: Calendar,
        color: 'text-blue-600',
        description: 'Per day rental'
      };
    }
    if (data.per_hour_rate) {
      return {
        type: 'hourly',
        primary: `Rs. ${parseInt(data.per_hour_rate).toLocaleString()}`,
        secondary: '/ hour',
        icon: Clock,
        color: 'text-purple-600',
        description: 'Hourly rental'
      };
    }
    if (data.weekly_rate) {
      return {
        type: 'weekly',
        primary: `Rs. ${parseInt(data.weekly_rate).toLocaleString()}`,
        secondary: '/ week',
        icon: Package,
        color: 'text-orange-600',
        description: 'Weekly package'
      };
    }
  }

  if (data.is_specific_route && data.fixed_fare) {
    return {
      type: 'fixed_route',
      primary: `Rs. ${parseInt(data.fixed_fare).toLocaleString()}`,
      secondary: data.distance ? `• ${data.distance} km` : 'Fixed Route',
      icon: Route,
      color: 'text-green-600',
      description: 'Complete route package'
    };
  }

  if (data.rate_per_km) {
    return {
      type: 'rate_km',
      primary: `Rs. ${data.rate_per_km}`,
      secondary: '/ km',
      icon: Navigation,
      color: 'text-red-600',
      description: 'Per kilometer rate'
    };
  }

  return {
    type: 'custom',
    primary: 'Custom Price',
    secondary: 'Contact for details',
    icon: DollarSign,
    color: 'text-gray-600',
    description: 'Custom pricing available'
  };
};

// Format date helper
const formatDate = (dateString) => {
  if (!dateString || dateString === "null" || dateString === "None") return "Not Set";
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  } catch (e) {
    return dateString;
  }
};

// Format time helper
const formatTime = (timeString) => {
  if (!timeString || timeString === "null" || timeString === "None") return "Not Set";
  try {
    if (timeString.includes(':')) {
      const [hours, minutes] = timeString.split(':');
      const hour = parseInt(hours);
      const ampm = hour >= 12 ? 'PM' : 'AM';
      const displayHour = hour % 12 || 12;
      return `${displayHour}:${minutes} ${ampm}`;
    }
    return timeString;
  } catch (e) {
    return timeString;
  }
};

// Format datetime
const formatDateTime = (dateTimeString) => {
  if (!dateTimeString || dateTimeString === "null" || dateTimeString === "None") return "Not Set";
  try {
    const date = new Date(dateTimeString);
    return date.toLocaleString('en-US', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  } catch (e) {
    return dateTimeString;
  }
};

export default function VehicleDetailsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams();
  const [vehicleData, setVehicleData] = useState(null);
  const [fullVehicleTimings, setFullVehicleTimings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timingsLoading, setTimingsLoading] = useState(false);

  useEffect(() => {
    if (location.state?.vehicleDetails) {
      const data = location.state.vehicleDetails;
      setVehicleData(data);
      setLoading(false);
      
      // Fetch full vehicle timings
      if (data.id) {
        fetchFullVehicleTimings(data.id);
      }
    } else {
      setLoading(false);
    }
  }, [location.state]);

const fetchFullVehicleTimings = async (vehicleId) => {
  setTimingsLoading(true);
  try {
    console.log("🔍 Vehicle ID for timings:", vehicleId);
    console.log("🔍 Full vehicle data:", vehicleData);
    
    // Check if vehicleId exists
    if (!vehicleId || vehicleId === "null" || vehicleId === "undefined") {
      console.error("❌ Invalid vehicle ID:", vehicleId);
      setFullVehicleTimings([]);
      return;
    }
    
    // CORRECTED ENDPOINT
    const endpoint = `http://127.0.0.1:8000/api/bookings/full-vehicle-timings/${vehicleId}/`;
    console.log(`📡 Calling endpoint: ${endpoint}`);
    
    const response = await fetch(endpoint);
    console.log("📊 Response status:", response);
    
    if (response.ok) {
      const data = await response.json();
      console.log("✅ Full vehicle timings received:", data);
      
      if (data.success && data.timings) {
        console.log("📅 Timings array:", data.timings);
        setFullVehicleTimings(data.timings);
      } else {
        console.warn("⚠️ No timings in response or success=false");
        setFullVehicleTimings([]);
      }
    } else {
      const errorText = await response.text();
      console.error("❌ Failed to fetch timings:", response.status, errorText);
      setFullVehicleTimings([]);
    }
  } catch (error) {
    console.error("🚨 Error fetching full vehicle timings:", error);
    setFullVehicleTimings([]);
  } finally {
    setTimingsLoading(false);
  }
};

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading vehicle details...</p>
        </div>
      </div>
    );
  }

  if (!vehicleData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Vehicle Not Found</h2>
          <p className="text-gray-600 mb-6">The vehicle details could not be loaded.</p>
          <button
            onClick={() => navigate(-1)}
            className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-indigo-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const displayImage = vehicleData.vehicle_image || defaultVehicleImage;
  const displayVehicleType = vehicleData.vehicle_type || "Premium Vehicle";
  const vehicleSeats = vehicleData.vehicle_seats || "N/A";
  const vehicleNumber = vehicleData.vehicle_number || "Not Available";
  const driverName = vehicleData.driver_name || "Professional Driver";
  const driverContact = vehicleData.driver_contact || "Contact not available";

  const pricing = getPricingDisplay(vehicleData);

  const handleBookNow = () => {
    const token = localStorage.getItem("accessToken");

    if (!token || token === "null" || token === "undefined" || token.trim() === "") {
      navigate("/login", {
        replace: true,
        state: {
          from: `/book-vehical/${id}`,
          vehicleDetails: vehicleData,
        },
      });
      return;
    }

    navigate(`/book-vehical/${id}`, {
      state: {
        vehicleDetails: vehicleData,
      },
    });
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white shadow-sm sticky top-0 z-40"
      >
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={handleGoBack}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-6 h-6 mr-2" />
              <span className="font-semibold">Back</span>
            </button>
            
            <h1 className="text-xl font-bold text-gray-900">Vehicle Details</h1>
            
            <div className="w-6"></div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Images & Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Vehicle Image */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-2xl shadow-lg overflow-hidden"
            >
              <img
                src={displayImage}
                alt={vehicleData.company_name}
                className="w-full h-96 object-cover"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = defaultVehicleImage;
                }}
              />
            </motion.div>

            {/* Vehicle Specifications */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-2xl shadow-lg p-6"
            >
              <h3 className="text-xl font-bold text-gray-900 mb-6">Vehicle Specifications</h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="flex items-center p-4 bg-gray-50 rounded-xl">
                  <Car className="w-8 h-8 text-blue-500 mr-4" />
                  <div>
                    <div className="text-sm text-gray-500">Vehicle Type</div>
                    <div className="font-semibold text-gray-900">{displayVehicleType}</div>
                  </div>
                </div>

                <div className="flex items-center p-4 bg-gray-50 rounded-xl">
                  <Users className="w-8 h-8 text-green-500 mr-4" />
                  <div>
                    <div className="text-sm text-gray-500">Seating Capacity</div>
                    <div className="font-semibold text-gray-900">{vehicleSeats} Seats</div>
                  </div>
                </div>

                {vehicleNumber && vehicleNumber !== "Not Available" && (
                  <div className="flex items-center p-4 bg-gray-50 rounded-xl">
                    <Shield className="w-8 h-8 text-indigo-500 mr-4" />
                    <div>
                      <div className="text-sm text-gray-500">Vehicle Number</div>
                      <div className="font-semibold text-gray-900">{vehicleNumber}</div>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>

            {/* Pricing Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl shadow-lg p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">Pricing Details</h3>
              </div>

              <div className={`flex items-center ${pricing.color} font-bold text-3xl mb-6 py-4 border-y border-gray-100`}>
                <pricing.icon className="w-8 h-8 mr-4" />
                <span>{pricing.primary}</span>
                <span className="text-xl font-semibold ml-3 text-gray-600">
                  {pricing.secondary}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {vehicleData.per_hour_rate && (
                  <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-200">
                    <Clock className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                    <div className="text-xl font-bold text-blue-700">Rs. {parseInt(vehicleData.per_hour_rate).toLocaleString()}</div>
                    <div className="text-sm text-blue-600">Per Hour</div>
                  </div>
                )}
                {vehicleData.per_day_rate && (
                  <div className="text-center p-4 bg-green-50 rounded-xl border border-green-200">
                    <Calendar className="w-8 h-8 text-green-600 mx-auto mb-2" />
                    <div className="text-xl font-bold text-green-700">Rs. {parseInt(vehicleData.per_day_rate).toLocaleString()}</div>
                    <div className="text-sm text-green-600">Per Day</div>
                  </div>
                )}
                {vehicleData.weekly_rate && (
                  <div className="text-center p-4 bg-orange-50 rounded-xl border border-orange-200">
                    <Package className="w-8 h-8 text-orange-600 mx-auto mb-2" />
                    <div className="text-xl font-bold text-orange-700">Rs. {parseInt(vehicleData.weekly_rate).toLocaleString()}</div>
                    <div className="text-sm text-orange-600">Weekly Package</div>
                  </div>
                )}
              </div>
            </motion.div>
          </div>

          {/* Right Column - Details & Timings */}
          <div className="space-y-6">
            {/* Vehicle Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl shadow-lg p-6"
            >
              <div>
                <h1 className="text-2xl font-bold text-gray-900 mb-2">
                  {vehicleData.company_name}
                </h1>
                <div className="flex items-center text-gray-600 mb-4">
                  <MapPin className="w-5 h-5 mr-2" />
                  <span className="text-lg">{vehicleData.location_address || "Location not specified"}</span>
                </div>
              </div>
            </motion.div>

            {/* Driver Information */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-2xl shadow-lg p-6"
            >
              <h3 className="text-xl font-bold text-gray-900 mb-4">Driver Information</h3>
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 rounded-full bg-indigo-100 flex items-center justify-center">
                  <Phone className="w-8 h-8 text-indigo-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-lg font-semibold text-gray-900">{driverName}</h4>
                  <div className="flex items-center mt-2 text-gray-600">
                    <Phone className="w-4 h-4 mr-2" />
                    <span className="font-medium">{driverContact}</span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* FULL VEHICLE BOOKING TIMINGS - SIMPLE */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white rounded-2xl shadow-lg p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <Car className="w-6 h-6 text-indigo-600 mr-3" />
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Full Vehicle Booking Timings</h3>
                    <p className="text-sm text-gray-500">This vehicle's booking schedule</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-full">
                  <span className="text-sm font-semibold">{fullVehicleTimings.length} Bookings</span>
                </div>
              </div>

              {timingsLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                  <p className="mt-2 text-sm text-gray-600">Loading booking timings...</p>
                </div>
              ) : fullVehicleTimings.length > 0 ? (
                <div className="space-y-4">
                  {fullVehicleTimings.map((timing, index) => (
                    <div 
                      key={index} 
                      className="border border-gray-200 rounded-xl p-4 hover:bg-gray-50 transition-colors"
                    >
                      {/* Booking Number */}
                      <div className="text-xs text-gray-500 mb-2">
                        Booking #{index + 1}
                      </div>
                      
                      {/* SIMPLE 3 FIELDS */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {/* Arrival Date */}
                        <div className="flex flex-col">
                          <div className="flex items-center text-gray-600 mb-1">
                            <CalendarDays className="w-4 h-4 mr-2 text-green-500" />
                            <span className="text-sm font-medium">Arrival Date</span>
                          </div>
                          <div className="font-semibold text-gray-900">
                            {formatDate(timing.arrival_date)}
                          </div>
                        </div>
                        
                        {/* Arrival Time */}
                        <div className="flex flex-col">
                          <div className="flex items-center text-gray-600 mb-1">
                            <Clock className="w-4 h-4 mr-2 text-blue-500" />
                            <span className="text-sm font-medium">Arrival Time</span>
                          </div>
                          <div className="font-semibold text-gray-900">
                            {formatTime(timing.arrival_time)}
                          </div>
                        </div>
                        
                        {/* Hold Expires At */}
                        <div className="flex flex-col">
                          <div className="flex items-center text-gray-600 mb-1">
                            <Timer className="w-4 h-4 mr-2 text-orange-500" />
                            <span className="text-sm font-medium">Hold Expires</span>
                          </div>
                          <div className="font-semibold text-gray-900">
                            {formatDateTime(timing.hold_expires_at)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CalendarDays className="w-8 h-8 text-gray-400" />
                  </div>
                  <h4 className="text-lg font-semibold text-gray-700 mb-2">No Full Vehicle Bookings</h4>
                  <p className="text-gray-500 text-sm">
                    This vehicle hasn't been booked for full vehicle rental yet.
                  </p>
                </div>
              )}

              <div className="mt-6 pt-6 border-t border-gray-100">
                <p className="text-xs text-gray-500 text-center">
                  Showing only arrival date, arrival time, and hold expiry
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Fixed Bottom Booking Bar */}
      <motion.div
        initial={{ opacity: 0, y: 100 }}
        animate={{ opacity: 1, y: 0 }}
        className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg"
      >
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-gray-900">{pricing.primary}</div>
              <div className="text-gray-600">{pricing.description}</div>
            </div>
            
            <div className="flex gap-4">
              <a 
                href={`tel:${driverContact}`}
                className="flex items-center px-6 py-3 border-2 border-indigo-600 text-indigo-600 rounded-xl font-semibold hover:bg-indigo-50 transition-colors"
              >
                <Phone className="w-5 h-5 mr-2" />
                Call Driver
              </a>
              
              <button
                onClick={handleBookNow}
                className="flex items-center px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg"
              >
                <CheckCircle className="w-5 h-5 mr-2" />
                Book Full Vehicle
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}