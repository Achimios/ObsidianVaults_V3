// =============================================================================
// calibration.rs — IMU 传感器校正
// =============================================================================

// >v<🌡传感器校正 - 温度补偿+零偏估计 - 温度每变化5°C必须重新校正
pub struct ImuCalibration {
    accel_bias: Vec3,
    gyro_bias: Vec3,
    temp_coeff: f32,
}

impl ImuCalibration {
    pub fn apply(&self, raw: Vec3, temperature: f32) -> Vec3 {
        let temp_offset = (temperature - 25.0) * self.temp_coeff;
        raw - self.accel_bias - Vec3::splat(temp_offset)
    }
}
