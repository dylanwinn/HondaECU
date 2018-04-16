#!/usr/bin/env python

from __future__ import division, print_function
import struct
import time
import sys
import os
import argparse

from HondaECU import *


if __name__ == '__main__':

	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('mode', choices=["read","write"], help="ECU mode")
	parser.add_argument('binfile', help="name of bin to read or write")
	parser.add_argument('--rom-size', default=256, type=int, help="size of ECU rom in kilobytes")
	db_grp = parser.add_argument_group('debugging options')
	db_grp.add_argument('--skip-power-check', action='store_true', help="don't test for k-line activity")
	db_grp.add_argument('--debug', action='store_true', help="turn on debugging output")

	args = parser.parse_args()

	if os.path.isabs(args.binfile):
		outfile = args.binfile
	else:
		outfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.binfile)

	ecu = HondaECU()

	if not args.skip_power_check:
		# In order to read flash we must send commands while the ECU's
		# bootloader is still active which is right after the bike powers up
		if ecu.kline():
			print("Turn off bike")
			while ecu.kline():
				time.sleep(.1)
		print("Turn on bike")
		while not ecu.kline():
			time.sleep(.1)
		time.sleep(.5)

	print("===============================================")
	print("Initializing ECU communications")
	ecu.init(debug=args.debug)
	time.sleep(.1)
	ecu.send_command([0x72],[0x00, 0xf0], debug=args.debug)
	# <- 0x02 0x04 0x00 0xfa

	print("===============================================")
	print("Entering Boot Mode")
	ecu.send_command([0x27],[0xe0, 0x48, 0x65, 0x6c, 0x6c, 0x6f, 0x48, 0x6f], debug=args.debug)
	ecu.send_command([0x27],[0xe0, 0x77, 0x41, 0x72, 0x65, 0x59, 0x6f, 0x75], debug=args.debug)
	time.sleep(.5)

	if args.mode == "read":
		print("===============================================")
		print("Dumping ECU to bin file")
		maxbyte = 1024 * args.rom_size
		nbyte = 0
		readsize = 8
		with open(outfile, "w") as fbin:
			t = time.time()
			while nbyte < maxbyte:
				info = ecu.send_command([0x82, 0x82, 0x00], [int(nbyte/65536)] + map(ord,struct.pack("<H", nbyte % 65536)) + [readsize], debug=args.debug)
				fbin.write(info[2])
				fbin.flush()
				nbyte += readsize
				if nbyte % 64 == 0:
					sys.stdout.write(".")
					sys.stdout.flush()
				if nbyte % 1024 == 0:
					n = time.time()
					sys.stdout.write(" %dkb %.02fbps\n" % (int(nbyte/1024),1024/(n-t)))
					t = n

	elif args.mode == "write":
		print("===============================================")
		print("Writing bin file to ECU")
		ecu.send_command([0x7d], [0x01, 0x01, 0x00], debug=args.debug)
		# <- 0x0d 0x0a 0x01 0x20 0x20 0x20 0x20 0x20 0x20 0x28 | data shows up in ECU bin
		ecu.send_command([0x7d], [0x01, 0x01, 0x01], debug=args.debug)
		# <- 0x0d 0x05 0x01 0x7b 0x72 | data shows up in ECU bin
		ecu.send_command([0x7d], [0x01, 0x01, 0x02], debug=args.debug)
		# <- 0x0d 0x07 0x01 0x00 0x00 0x00 0xeb
		ecu.send_command([0x7d], [0x01, 0x01, 0x03], debug=args.debug)
		# <- 0x0d 0x09 0x01 0x01 0x00 0x00 0x00 0x00 0xe8 | data shows up in ECU bin

		# This looks like a seed/key challenge/response
		ecu.send_command([0x7d], [0x01, 0x02, 0x50, 0x47, 0x4d], debug=args.debug)
		# <- 0x0d 0x05 0x02 0x00 0xec
		ecu.send_command([0x7d], [0x01, 0x03, 0x2d, 0x46, 0x49], debug=args.debug)
		# <- 0x0d 0x05 0x03 0x00 0xeb

		ecu.send_command([0x7e], [0x01, 0x01, 0x00], debug=args.debug)
		# <- 0x0e 0x05 0x01 0x10 0xdc | data shows up in ECU bin

		time.sleep(11)

		ecu.send_command([0x7e], [0x01, 0x02], debug=args.debug)
		# <- 0x0e 0x07 0x02 0x00 0x6c 0x54 0x29

		ecu.send_command([0x7e], [0x01, 0x03, 0x00, 0x00], debug=args.debug)
		# <- 0x0e 0x05 0x03 0x00 0xea

		ecu.send_command([0x7e], [0x01, 0x01, 0x00], debug=args.debug)
		# <- 0x0e 0x05 0x01 0x10 0xdc

		ecu.send_command([0x7e], [0x01, 0x0b, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff], debug=args.debug) #  | data shows up in ECU bin
		# <- 0x0e 0x05 0x0b 0x00 0xe2

		ecu.send_command([0x7e], [0x01, 0x01, 0x00], debug=args.debug)
		# <- 0x0e 0x05 0x01 0x20 0xcc

		ecu.send_command([0x7e], [0x01, 0x0e, 0x01, 0x90], debug=args.debug)
		# <- 0x0e 0x04 0x0e 0xe0

		ecu.send_command([0x7e], [0x01, 0x01, 0x01], debug=args.debug)
		# <- 0x0e 0x06 0x01 0x00 0x00 0xeb

		ecu.send_command([0x7e], [0x01, 0x04, 0xff], debug=args.debug)
		# <- 0x0e 0x05 0x04 0x00 0xe9

		ecu.send_command([0x7e], [0x01, 0x01, 0x00], debug=args.debug)
		# <- 0x0e 0x05 0x01 0x20 0xcc

		ecu.send_command([0x7e], [0x01, 0x05], debug=args.debug)
		# <- 0x0e 0x05 0x05 0x01 0xe7

		### SEND data

		# -> 0x7e 0x06 0x01 0x01 0x00 0x7a
		# <- 0x0e 0x05 0x01 0x40 0xac

		# -> 0x7e 0x05 0x01 0x09 0x73
		# <- 0x0e 0x05 0x09 0x00 0xe4

		# -> 0x7e 0x06 0x01 0x01 0x00 0x7a
		# <- 0x0e 0x05 0x01 0x50 0x9c

		# -> 0x7e 0x05 0x01 0x0a 0x72
		# <- 0x0e 0x05 0x0a 0x00 0xe3

		# -> 0x7e 0x06 0x01 0x01 0x00 0x7a
		# <- 0x0e 0x05 0x01 0x50 0x9c

		# -> 0x7e 0x05 0x01 0x0c 0x70
		# <- 0x0e 0x05 0x0c 0x00 0xe1

		# -> 0x7e 0x06 0x01 0x01 0x00 0x7a
		# <- 0x0e 0x05 0x01 0x50 0x9c

		# -> 0x7e 0x05 0x01 0x0d 0x6f
		# <- 0x0e 0x05 0x0d 0x0f 0xd1

		# -> 0x7e 0x06 0x01 0x01 0x00 0x7a
		# <- 0x0e 0x05 0x01 0x0f 0xdd


	print("===============================================")
