#version 330 core
out vec4 fragColor;

in vec4 clipCoords;

uniform samplerCube u_texture_skybox;
uniform mat4 m_invProjView;
uniform vec3 u_sun_dir;  // Normalized sun direction

// **Constants**
const float VERY_NIGHT_HEIGHT = -0.20;
const float NIGHT_HEIGHT = -0.10;
const float SUNRISE_START = -0.05;  // New transition start (avoids sudden glow pop)
const float DAY_HEIGHT = 0.25;

const vec3 SUN_COLOR_NIGHT = vec3(1.0, 0.3, 0.1);    // Deep red sun at low altitude
const vec3 SUN_COLOR_DAY = vec3(1.0, 0.9, 0.6);      // Bright white sun when high

const float SUN_CORE_RADIUS = 0.02;                  // Radius of full-color sun core
const float SUN_FADE_RADIUS = 0.04;                  // Slight gradient at the edge of the sun core

const float HALO_RADIUS_DAY = 2.0;                  // Smaller halo when sun is high
const float HALO_RADIUS_NIGHT = 3.0;                 // Wider halo when sun is low

const float HALO_SPREAD_DAY = 0.4;                   // Sharper glow at midday
const float HALO_SPREAD_NIGHT = 0.6;                 // Broader, more lateral spread at sunset/night

const float HALO_HORIZONTAL_FACTOR_NIGHT = 4.0;      // Strength of horizontal spreading of the glow at night

const float SUN_GLOW_FACTOR_DAY = 4.0;
const float SUN_GLOW_FACTOR_NIGHT = 10.0;             // Adjusts intensity of glow (higher = stronger glow)

// **Gamma Correction**
vec3 gammaCorrect(vec3 color, float value) {
    return pow(color, vec3(1.0 / value));
}

void main() {
    vec4 worldCoords = m_invProjView * clipCoords;
    vec3 texCubeCoord = normalize(worldCoords.xyz / worldCoords.w);
    vec4 skyColor;

    // **Sky Brightness Factor**
    float sunAltitude = u_sun_dir.y;
    vec4 lowColor = mix(vec4(0.2, 0.4, 0.7, 1.0), vec4(1.0, 1.0, 1.0, 1.0), sunAltitude);
    skyColor = mix(lowColor, vec4(0.0, 0.37, 0.81, 1.0), pow(abs(texCubeCoord.y + 0.1), 0.5));
    skyColor = texture(u_texture_skybox, texCubeCoord);


    // **Fix: Smooth fade-in from full black instead of instant jump**
    float fullBlackFactor = smoothstep(VERY_NIGHT_HEIGHT, NIGHT_HEIGHT, sunAltitude); // 0 → 1 transition
    if (sunAltitude < VERY_NIGHT_HEIGHT) {
        fragColor = vec4(0.02, 0.02, 0.05, 1.0);
        return;
    }

    float skyDarkness = smoothstep(NIGHT_HEIGHT, DAY_HEIGHT, sunAltitude); // 0 = bright, 1 = dark

    // **Fix: Smooth sunrise glow instead of instant pop**
    float sunriseFactor = smoothstep(NIGHT_HEIGHT, SUNRISE_START, sunAltitude);  // Soft fade-in

    // **Sun Position and Distance Calculation**
    float sunDistance = length(texCubeCoord - u_sun_dir);

    // **Sun Core & Halo Colors**
    vec3 sunColor = mix(SUN_COLOR_NIGHT, SUN_COLOR_DAY, skyDarkness);

    // **Halo Effect Scaling Based on Sun Altitude**
    float haloSize = mix(HALO_RADIUS_NIGHT, HALO_RADIUS_DAY, skyDarkness);
    float haloSpread = mix(HALO_SPREAD_NIGHT, HALO_SPREAD_DAY, skyDarkness);

    // **Directional Horizon Enhancement**
    float horizonFactor = clamp(1.0 - abs(texCubeCoord.y), 0.0, 1.0); // Strong near horizon, fades upward
    float horizonHaloBoost = mix(1.0, HALO_HORIZONTAL_FACTOR_NIGHT, horizonFactor);

    haloSize *= horizonHaloBoost;
    haloSpread *= mix(1.0, 0.5, horizonFactor); // Soften the glow near the horizon

    // **Sun Core Glow (Ensuring a Hard Edge)**
    float sunCore = smoothstep(SUN_FADE_RADIUS, SUN_CORE_RADIUS, sunDistance); // Small, sharp core

    // **Halo Falloff (Smoother Transition)**
    float sunGlowFactor = mix(SUN_GLOW_FACTOR_NIGHT, SUN_GLOW_FACTOR_DAY, skyDarkness);
    float sunGlow = exp(-pow(sunDistance * haloSize, haloSpread)) * sunGlowFactor; // Glow strength scaled by factor
    sunGlow *= mix(pow(horizonFactor, 1), 1.0, skyDarkness);

    // **Dark Sky Transition (Full black fades in smoothly)**
    vec3 nightSky = vec3(0.02, 0.02, 0.05);
    vec3 skyFinalColor = mix(nightSky, skyColor.rgb, skyDarkness * fullBlackFactor);

    // **Fix: Apply sunriseFactor so glow fades in smoothly**
    skyFinalColor += sunriseFactor * (sunGlow * sunColor * 0.5); // Halo effect (scaled)
    skyFinalColor += sunriseFactor * (sunCore * sunColor);       // Defined sun shape

    fragColor = vec4(skyFinalColor, 1.0);
}