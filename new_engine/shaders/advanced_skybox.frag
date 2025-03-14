#version 330 core
out vec4 fragColor;

in vec4 clipCoords;

uniform samplerCube u_texture_skybox;
uniform mat4 m_invProjView;
uniform vec3 u_sun_dir;  // Normalized sun direction

// **Constants**
const float NIGHT_HEIGHT = -0.05;
const float DAY_HEIGHT = 0.15;

const vec3 SUN_COLOR_NIGHT = vec3(1.0, 0.3, 0.1); // Deep red sun at low altitude
const vec3 SUN_COLOR_DAY = vec3(1.0, 0.9, 0.6);   // Bright white sun when high

const float SUN_CORE_RADIUS = 0.02;    // Radius of full-color sun core
const float SUN_FADE_RADIUS = 0.04;    // Slight gradient at the edge of the sun core

const float HALO_RADIUS_DAY = 10.0;     // Smaller halo when sun is high
const float HALO_RADIUS_NIGHT = 3.0;  // Wider halo when sun is low

const float HALO_SPREAD_DAY = 2.5;     // Sharper glow at midday
const float HALO_SPREAD_NIGHT = 0.8;   // Broader, more lateral spread at sunset/night

const float HALO_HORIZONTAL_FACTOR_NIGHT = 5.0; // Strength of horizontal spreading of the glow at night

const float SUN_GLOW_FACTOR = 5.0;     // Adjusts intensity of glow (higher = stronger glow)


// Apply gamma correction (common value is 2.2)
vec3 gammaCorrect(vec3 color, float value) {
    return pow(color, vec3(1.0 / value));
}

void main() {
    vec4 worldCoords = m_invProjView * clipCoords;
    vec3 texCubeCoord = normalize(worldCoords.xyz / worldCoords.w);
    vec4 skyColor = texture(u_texture_skybox, texCubeCoord);

    // **Sky Brightness Factor**
    float sunAltitude = u_sun_dir.y;
    float skyDarkness = smoothstep(DAY_HEIGHT, NIGHT_HEIGHT, sunAltitude); // 0 = bright, 1 = dark

    // **Sun Position and Distance Calculation**
    float sunDistance = length(texCubeCoord - normalize(u_sun_dir));

    // **Sun Core & Halo Colors**
    vec3 sunColor = mix(SUN_COLOR_NIGHT, SUN_COLOR_DAY, smoothstep(NIGHT_HEIGHT, DAY_HEIGHT, sunAltitude));

    // **Halo Effect Scaling Based on Sun Altitude**
    float haloSize = mix(HALO_RADIUS_NIGHT, HALO_RADIUS_DAY, smoothstep(NIGHT_HEIGHT, DAY_HEIGHT, sunAltitude));
    float haloSpread = mix(HALO_SPREAD_NIGHT, HALO_SPREAD_DAY, smoothstep(NIGHT_HEIGHT, DAY_HEIGHT, sunAltitude));

    // **Directional Horizon Enhancement**
    float horizonFactor = 1.0 - abs(texCubeCoord.y); // Strong near horizon, fades upward
    if (sunAltitude < DAY_HEIGHT) {
        haloSize *= mix(1.0, HALO_HORIZONTAL_FACTOR_NIGHT, horizonFactor); // Expand halo horizontally
        haloSpread *= mix(1.0, 0.5, horizonFactor); // Soften the glow near the horizon
    }

    // **Sun Core Glow (Ensuring a Hard Edge)**
    float sunCore = smoothstep(SUN_FADE_RADIUS, SUN_CORE_RADIUS, sunDistance); // Small, sharp core

    // **Halo Falloff (Smoother Transition)**
    float sunGlow = exp(-pow(sunDistance * haloSize, haloSpread)) * SUN_GLOW_FACTOR; // Glow strength scaled by factor

    // **Dark Sky Transition**
    vec3 nightSky = vec3(0.02, 0.02, 0.05);
    vec3 skyFinalColor = mix(skyColor.rgb, nightSky, skyDarkness);

    // **Blend Sun Glow & Core**
    skyFinalColor += sunGlow * sunColor * 0.5; // Halo effect (scaled by SUN_GLOW_FACTOR)
    skyFinalColor += sunCore * sunColor;       // Defined sun shape

    fragColor = vec4(gammaCorrect(skyFinalColor, 2.2), 1.0);
    fragColor = vec4(skyFinalColor, 1.0);
}
