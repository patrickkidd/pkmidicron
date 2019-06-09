#!/usr/bin/env ruby

require 'xcodeproj'


def find_ref target, fname
    target.source_build_phase.files.each do |pbx_build_file|
        if pbx_build_file.file_ref.real_path.to_s.include? fname
            return pbx_build_file.file_ref.real_path.to_s
        end
    end
    return nil
end


if ARGV[0] == 'osx'
    fpath = 'build/osx/PKMidiCron.xcodeproj'
    project = Xcodeproj::Project.open(fpath)
    project.targets.each do |target|
        if target.name == "PKMidiCron"
            ref = find_ref(target, "darwin64.S")
            if not ref.nil?
                puts "**** Found darwin64.S in target, exiting"
            else
                # fnames = []
                # ARGV.each_with_index do |key, value|
                #     if key > 1
                #         fnames.push(value)
                #         puts "found: #{value}"
                #     end
                # end
                file_ref = project.reference_for_path('/Users/patrick/dev/vendor/sysroot-macos-64/src/Python-3.6.4-patched/Modules/_ctypes/libffi_osx/x86/darwin64.S')
                puts "**** darwin64.S not found in target. Adding: #{file_ref}"
                target.add_file_references([file_ref])
                project.mark_dirty!
                project.save
                break
            end
        end
    end
end
