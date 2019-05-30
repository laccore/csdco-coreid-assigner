from gooey import Gooey, GooeyParser
import renamer

@Gooey(program_name='CSDCO CoreID Applier')
def main():
  parser = GooeyParser(description='Apply CoreIDs to the output from Geotek MSCL software.')
  parser.add_argument('input_file', widget='FileChooser', metavar='Input file (without CoreIDs)', help='Name of input file.')
  parser.add_argument('corelist', widget='FileChooser', metavar='Core list file', help='CSV in the format section #,coreID')
  parser.add_argument('-o', '--output_filename', metavar='Output filename', type=str, help='Name of the output file.')
  parser.add_argument('-v', '--verbose', metavar='Verbose', action='store_true', help='Print troubleshooting information.')
  parser.add_argument('-s', '--section_column', type=int, metavar='Section Number Column', help='Column number the section numbers are in (count starts at 0).')
  parser.add_argument('-d', '--depth_column', type=int, metavar='Section Depth Column', help='Column number the section depths are in (count starts at 0).')

  args = parser.parse_args()

  renamer.apply_names(args.input_file,
                      args.corelist,
                      section_column=args.section_column,
                      depth_column=args.depth_column,
                      output_filename=args.output_filename,
                      verbose=args.verbose)


if __name__ == '__main__':
  main()
