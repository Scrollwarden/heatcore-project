



float height;
vec3 normal;
do {
    height = getHeight(position);
    normal = getNormal(position);
} while (height < 0)