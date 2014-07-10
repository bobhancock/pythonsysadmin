package main

import (
    //"fmt"
    "math"
	"os"
	"flag"
	"log"
	"runtime/pprof"
)

var cpuprofile = flag.String("cpuprofile", "", "write cpu profile to file")
var memprofile = flag.String("memprofile", "", "write memory profile to this file")

// Reverse the slice
func reverse(r []int) []int {
	n, h := len(r), len(r)/2
	for i := 0; i < h; i++ {
		r[i], r[n-1-i] = r[n-1-i], r[i]
	}
	return r
}

// TODO Depth first search for second element
// Once calculated launch calc of rest of row in a goroutine
// Store result in a map[rownum][]int
// Use big integer to prevent overflow if maxrows > what?
// Make maxrows a command line arg
func main() {
	flag.Parse()
	//Setup  profiling
	if *cpuprofile != "" {
		f, err := os.Create(*cpuprofile)
		if err != nil {
			log.Fatal(err)
		}
		pprof.StartCPUProfile(f)
		defer pprof.StopCPUProfile()
	}

	if *memprofile != "" {
        f, err := os.Create(*memprofile)
        if err != nil {
            log.Fatal(err)
        }
        pprof.WriteHeapProfile(f)
        f.Close()
        return
    }

	m := 10000 //max iterations
	prev := []int{1}
    //fmt.Println(prev)

    for row := 1; row < m; row++ {
		curr := make([]int,1,row)
		curr[0] = 1

		mid := (row / 2) 
		var right int 
		if math.Fmod(float64(row), 2.0) == 0 {
			right = mid
		} else {
			right = mid + 1
		}
		
		for j := 1; j < mid; j++ {
			curr = append(curr, prev[j - 1] + prev[j])
		}
		
		s := make([]int, right)
		r := curr[0:right]
		copy(s,r)
		rev := reverse(s)
		curr = append(curr, rev...)
//		fmt.Println(curr)
		prev = curr
    }
 }