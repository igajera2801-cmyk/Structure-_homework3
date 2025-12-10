// Example program demonstrating variable watching
// Run with: python runner.py example.t watch=counter

print "=== Variable Watch Demo ==="

// Initialize counter
counter = 0
print "Starting loop..."

// Loop that modifies counter
while (counter < 5) {
    counter = counter + 1
    print counter
}

print "Loop finished!"

// More modifications to counter
counter = counter * 2
print "Doubled counter:"
print counter

// Some other variables (won't trigger watch for 'counter')
x = 100
y = 200

// Final modification
counter = 0
print "Reset counter to:"
print counter

print "=== Done ==="
