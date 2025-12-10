// Advanced watch demo - shows line/column tracking

print "=== Watch Location Tracking Demo ==="

// Multiple assignments on different lines
x = 1
x = 2
x = 3

// Assignment inside a condition
if (TRUE) {
    x = 10
}

// Nested blocks
if (TRUE) {
    if (TRUE) {
        x = 20
    }
}

// In a loop
i = 0
while (i < 3) {
    x = i * 10
    i = i + 1
}

// Complex expression result
x = (5 + 3) * 2

print "Final x value:"
print x

print "=== Done ==="
