"""
A template for a single threaded producer and multi-threaded consumer that emits

producers -> consumers -> output

The producers emit a collection of files under the base directories.

The consumers read the file names off the the queue, obtain the stats of the current file,
place them on an output queue.

The output thread is single threaded and reads from the output wqueue one at a time.

N.B.  This is a template.  Place appropriate logging and exception trapping as needed.
"""
import sys
import os
import threading
from Queue import Queue

__author__ = "Bob Hancock <hancock.robert@gmail.com>"

def output(output_func, output_q, outfile):
    """
    Create only one thread for output so that the results are synchronized.
    
    Args:
        output_func - the function that emits the data.
        output_q - the q from which to read.
        outfile - name of the output file.  If it exists it will be overwritten.
    """
    th = threading.Thread(name="output", target=output_func, args=(output_q, outfile))
    th.daemon = True
    th.start()

    return th


def write_output(output_q, outfile):
    """
    Emit each fname,mtime tuple on the output queue.
    """
    with open(outfile, "w") as fh:
        while True:
            output = output_q.get()
            if output == None:
                break
    
            fname, mtime = output
            fh.write("fname={f}|mtime={m}\n".format(f=fname, m=mtime))
    
        output_q.task_done()

def consumer(max_consumers, consumer_func, consumer_q, output_q):
    """
    Consume the file names from the consumer_q, get the file stats and place
    the data on the output queue.
    
    Args:
        max_consumers - the number of consumer threads.
        consumer_func - the function to execute in the thread.
        consumer_q - the queue from which the consumer reads.
        output_q - the queue with the results data that will be written to a file.
        
    Return:
        A tuple of consumer threads.
    """
    consumers = []
    for i in range(max_consumers):
        th = threading.Thread(name="consumer", target=consumer_func, args=(consumer_q, output_q))
        th.daemon = True
        consumers.append(th)
        th.start()

    return tuple(consumers)


def stat_file(consumer_q, output_q):
    """
    For this example, we only extract the mtime, but you could make this as comples
    as you like.
    
    Args:
        consumer_q - the queue with the filenames (input)
        output_q - the output queue that will be run in only one thread so that
                    that data is sequenced.
    """
    while True:
        fname = consumer_q.get()
        if fname == None:
            break

        # Get the modification time of the file and place the file name and
        # the mtime on the output queue.
        output_q.put( (fname, os.path.getmtime(fname)) )

    consumer_q.task_done()

def producer(base_dirs, producer_func, consumer_q):
    """
    Args:
        base_dirs - an iterable of base directory names.
        producer_func - the function to execute in the threads.
        consumer_q - the to which the producers write their results.
        
    Return:
        A tuple of producer threads.
    """
    producers = []
    for dr in base_dirs:
        th = threading.Thread(name="producer", target=producer_func,
                              args=(dr, consumer_q))
        th.daemon = True
        producers.append(th)
        th.start()

    return (producers)


def find_files(base_dir, consumer_q):                         
    """
    Find each file under the base dir and place it on the consumer queue.
    """
    for dirpath, dirs, files in os.walk(base_dir, topdown=False):
        for f in files:
            fullpath = os.path.join(dirpath, f)
            if os.path.isfile(fullpath):
                consumer_q.put(fullpath)


def main():
   # These variables can be retreived from either a settings or configuration file. 
    base_dirs = ("/var/tmp/dirwalk",)
    max_consumers = 4
    outfile = "/var/tmp/consumerprod.txt"
    
    producer_func = find_files
    consumer_func = stat_file
    output_func = write_output

    consumer_q = Queue()
    output_q = Queue()
    
    # Start the processes in the order from last to first, so that your producer
    # is ths last to start.
    output_thread = output(output_func, output_q, outfile)
    consumers = consumer(max_consumers, consumer_func, consumer_q, output_q)
    producers = producer(base_dirs, producer_func, consumer_q)
    for prod in producers:
        prod.join()

    # Now that the producers are finished, place a sentinel on the queues for each
    # consumer process to signify the end of the queue.
    for i in range(max_consumers):
        consumer_q.put(None)

    # Wat for the consumers to complete.
    for c in consumers:
        c.join()

    # Place the sentinel on the output queue.
    output_q.put(None)
    output_thread.join()

    print("Program complete")

if __name__ == "__main__":
    sys.exit(main())
