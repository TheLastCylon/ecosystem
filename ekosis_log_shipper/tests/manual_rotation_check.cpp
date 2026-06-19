// Manual proof: TrackedFile must not lose a line across a rotation that
// happens exactly between two poll() calls, simulating RotatingFileHandler's
// rename-then-fresh-file rollover.
#include "../src/tracked_file.hpp"

#include <cstdio>
#include <fstream>
#include <iostream>

int main() {
    const std::string path = "/tmp/shipper_rotation_test.log";

    std::remove(path.c_str());
    std::remove((path + ".1").c_str());

    { std::ofstream f(path); f << "line-before-rotation-1\n"; }

    TrackedFile tf(path);
    auto first = tf.poll();
    for (auto& l : first) std::cout << "got: " << l << "\n";

    { std::ofstream f(path, std::ios::app); f << "line-before-rotation-2\n"; }

    // Simulate RotatingFileHandler's rollover: rename active file away,
    // open a fresh empty file at the original path.
    std::rename(path.c_str(), (path + ".1").c_str());
    { std::ofstream f(path); f << "line-after-rotation-1\n"; }

    auto second = tf.poll();
    for (auto& l : second) std::cout << "got: " << l << "\n";

    bool ok = first.size() == 1 && first[0] == "line-before-rotation-1"
           && second.size() == 2
           && second[0] == "line-before-rotation-2"
           && second[1] == "line-after-rotation-1";

    std::cout << (ok ? "PASS" : "FAIL") << "\n";
    return ok ? 0 : 1;
}
