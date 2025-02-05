#version 330 core

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in uint in_id;

out vec3 inNormal;
out vec3 waveNormal;
out vec3 fragPos;
out vec3 inColor;
out float fragRealHeight;
out float fragOriginalHeight;

uniform vec3[256] colors;
uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float time;

#define NUM_WAVES 4
#define PI 3.14159265358979323846

// Simple hash function for pseudo-random noise
float hash(float x, float z) {
    ivec2 i = ivec2(floor(x), floor(z)); // Convert to integer coordinates
    int n = i.x * 15731 + i.y * 789221;
    n = (n << 13) ^ n;
    return 1.0 - float((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0;
}

// Simple Perlin-like gradient noise function
float gradientNoise(float x, float z) {
    ivec2 i = ivec2(floor(x), floor(z)); // Convert to integer coordinates
    float xf = x - float(i.x);
    float zf = z - float(i.y);
    
    float n00 = hash(float(i.x), float(i.y));
    float n10 = hash(float(i.x + 1), float(i.y));
    float n01 = hash(float(i.x), float(i.y + 1));
    float n11 = hash(float(i.x + 1), float(i.y + 1));
    
    float u = xf * xf * (3.0 - 2.0 * xf); // Smoothstep interpolation
    float v = zf * zf * (3.0 - 2.0 * zf);
    
    float nx0 = mix(n00, n10, u);
    float nx1 = mix(n01, n11, u);
    
    return mix(nx0, nx1, v);
}

// Improved Perlin noise function with multiple octaves
float perlinNoise(float x, float z, float t) {
    float agitation = 0.01;
    float total = 0.0;
    float frequency = 1.5;
    float amplitude = 2.0;
    float persistence = 0.5;
    int octaves = 6;

    for (int i = 0; i < octaves; i++) {
        // Add time as a third dimension to simulate evolving waves
        total += gradientNoise(x * frequency + agitation * sin(t) * t, z * frequency + agitation * cos(t) * t) * amplitude;
        frequency *= 2.0;
        amplitude *= persistence;
    }
    
    return total;
}

// Main height function using only Perlin noise (with time)
float heightValue(float x, float z) {
    float noiseValue = perlinNoise(x, z, time);
    return 0.015 * (noiseValue - 0.5);
}

void main() {
    fragOriginalHeight = in_position.y;
    inNormal = normalize(mat3(transpose(inverse(m_model))) * in_normal);

    vec3 position = in_position;
    
    if (fragOriginalHeight <= 0) {
        float dx = 0.01;
        float dz = 0.01;
        float h = heightValue(position.x, position.z);
        position.y = h;

        // Compute wave normal using finite difference method
        float h1 = heightValue(in_position.x + dx, in_position.z);
        float h2 = heightValue(in_position.x, in_position.z + dz);

        vec3 tangentX = vec3(dx, h1 - h, 0);
        vec3 tangentZ = vec3(0, h2 - h, dz);
        vec3 computedNormal = normalize(cross(tangentZ, tangentX));

        // Transform normal into world space
        waveNormal = normalize(mat3(transpose(inverse(m_model))) * computedNormal);
    } else {
        waveNormal = inNormal;
    }

    fragRealHeight = position.y;
    fragPos = vec3(m_model * vec4(position, 1.0));
    gl_Position = m_proj * m_view * m_model * vec4(position, 1.0);
    inColor = colors[in_id];
}