#version 330 core

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec3 in_color;

out vec3 inNormal;
out vec3 fragPos;
out vec3 inColor;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;

void main() {
    inNormal = normalize(mat3(transpose(inverse(m_model))) * in_normal);
    fragPos = vec3(m_model * vec4(in_position, 1.0));
    gl_Position = m_proj * m_view * m_model * vec4(in_position, 1.0);
    inColor = in_color;
}