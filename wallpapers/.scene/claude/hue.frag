#version 440
// hue.frag (→ hue.frag.qsb: /usr/lib64/qt6/bin/qsb --qt6 -o hue.frag.qsb hue.frag): turns a picture's hues by
// `shift` (0–1 of the colour wheel) and scales how colourful it is by `sat`, so the scene follows the album's colour
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float shift;
    float sat;
};
layout(binding = 1) uniform sampler2D source;

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + 1e-10)), d / (q.x + 1e-10), q.x);
}
vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}
void main() {
    vec4 c = texture(source, qt_TexCoord0);
    vec3 rgb = c.a > 0.0 ? c.rgb / c.a : c.rgb;   // (premultiplied)
    vec3 h = rgb2hsv(rgb);
    h.x = fract(h.x + shift);
    h.y = clamp(h.y * sat, 0.0, 1.0);
    fragColor = vec4(hsv2rgb(h) * c.a, c.a) * qt_Opacity;
}
