#
# Spec file generated by kdist version v0.4-10-g4f9a
#
%define name		kernel-server
%define version		3.3.0
%define src_uname_r	3.3.0-1
%define source_release	1
%define build_release	1%{nil}
%define archive		kernel-server-3.3.0-1.1

%define build_srpm	1
%define no_source	1

%define _source_path	/usr/src/linux-%{src_uname_r}
%if %no_source
%define source_path	%{_source_path}/
%else
%define source_path	./
%endif

# binary specific macros
%define flavour		server
%define uname_r		3.3.0-1.1-server
%define exclusive	x86_64
%define kdevel_path	/usr/src/devel/%{uname_r}

%ifarch x86_64
%define asm		x86_64
%define asmarch		x86
%endif

%bcond_without devel
%bcond_without debuginfo

Name:			%{name}
Summary:		The Linux Kernel for Mandriva %{flavour} systems
URL:			http://www.kernel.org
Version:		%{version}
Release:		%mkrel %{source_release}.%{build_release}
License:		GPLv2
Group:			System/Kernel and hardware
Provides:		kernel = %{version}-%{release}
ExclusiveArch:		%{exclusive}
BuildRoot:		%{_tmppath}/%{name}-%{version}-root
Source0:		%{archive}.tar.bz2
Source1:		%{uname_r}-x86_64-defconfig
Source2:		%{uname_r}-x86-develfiles.list
Source3:		%{uname_r}-develfiles.list
Source4:		%{uname_r}-output-develfiles.list
Requires:		kernel-firmware
Requires(pre):		bootloader-utils
Requires(pre):		mkinitrd
Requires(pre):		module-init-tools
BuildRequires:		module-init-tools
%if %no_source
BuildRequires:		kernel-source = %{version}-%{mkrel %{source_release}}
%endif

%define debug_package	%{nil}
%define __check_files	%{nil}

# Go away rpmlint, life is too short !
%define _build_pkgcheck_set	%{nil}
%define _build_pkgcheck_srpm	%{nil}

%if %{with devel}
%package devel
Summary:		The minimal Linux Kernel for building %{flavour} kernel modules
Provides:		kernel-devel = %{version}-%{release}
Group:			Development/Kernel
AutoReqProv:		no
Requires:		%{name} = %{version}-%{release}
%endif

%if %{with debuginfo}
%global __debug_package	1

%package debuginfo
Summary:		The debug information for the %{flavour} kernel
Provides:		kernel-debuginfo = %{version}-%{release}
Group:			Development/Debug
AutoReqProv:		no
%if %{no_source}
Suggests:		kernel-source = %{version}-%{mkrel %{source_release}}
%endif
%endif

%description -n %{name}
This kernel is compiled for server use, single or multiple
processor(s)/core(s), using no preempt, HZ_100, CFS cpu scheduler and
cfq i/o scheduler.

This kernel relies on in-kernel smp alternatives to switch between up
& smp mode depending on detected hardware. To force the kernel to boot
in single processor mode, use the 'nosmp' boot parameter.

%if %{with devel}
%description -n %{name}-devel
This package provides headers, makefiles and a couple of others files
sufficient to build external modules for %{name}.
%endif

%if %{with debuginfo}
%description -n %{name}-debuginfo
This package provides the %{name}'s debug information required
by some binary object tools like kgdb, perf, etc...
%endif

%if %{build_srpm}

%prep
%setup -q -n %{archive}
cp %{_sourcedir}/%{uname_r}-%{asm}-defconfig .config

%if %no_source
make -C %{source_path} O=$(pwd) outputmakefile
%endif

# localversion is updated here so the user can increase
# the release number anytime.
echo -n .%{build_release} >localversion

%else

%prep
%setup -T -D -n %{archive}

%endif

%build
make oldconfig
# Sanity check uname_r (it can be modified)
test %{uname_r} = $(make -s kernelrelease)

%if %build_srpm
make %{?_smp_mflags}
%endif

%install
if grep -q CONFIG_MODULES=y .config
then
	#
	# Don't specify parallel jobs here since it may break modules
	# installation somehow...
	#
	make -s INSTALL_MOD_PATH=%{buildroot} modules_install

	#
	# Mark all kernel modules as executable so they will be
	# stripped and their corresponding debug info files will be
	# generated if needed.
	#
	find %{buildroot} -name \*.ko -exec chmod u+x {} \;
else
	mkdir -p %{buildroot}/lib/modules/%{uname_r}
fi
mkdir -p %{buildroot}/boot

# symlinks are always created.
ln -snf %{kdevel_path} %{buildroot}/lib/modules/%{uname_r}/build
ln -snf build %{buildroot}/lib/modules/%{uname_r}/source
%ifarch x86_64
cp arch/x86/boot/bzImage %{buildroot}/boot/vmlinuz-%{uname_r}
cp System.map %{buildroot}/boot/System.map-%{uname_r}
cp .config %{buildroot}/boot/config-%{uname_r}
%endif

%if %{with devel}
mkdir -p %{buildroot}%{kdevel_path}

%if %no_source
cd source
%endif

for list in %{_sourcedir}/%{uname_r}{,-%asmarch}-develfiles.list; do
	tar -cf - --files-from=$list | tar -xf - -C %{buildroot}%{kdevel_path}
done

%if %no_source
cd -
%endif

list=%{_sourcedir}/%{uname_r}-output-develfiles.list
tar -cf - --files-from=$list | tar -xf - -C %{buildroot}%{kdevel_path}

# localversion might exist when generating a rpm package, in that case
# use it.
test -f localversion && cp localversion %{buildroot}%{kdevel_path}

make -C %{buildroot}%{kdevel_path} modules_prepare
%endif

%if %{with debuginfo}
#
# All this mess in order to have vmlinux build-id unmodified, its
# symtab section preserved and the generated source codes included in
# the debuginfo package.
#
# It also handles the different packaging cases (srpm, srpm+source,
# rpm), with more or less restrictions. But for the 'official' one,
# that is srpm using the kernel-source package, there shouldn't be
# any.
#
%define debuginfodir /usr/lib/debug

#
# Install vmlinux in a temporary (and arbitrary) place with the exec
# bit set so find-debuginfo will consider it.
#
cp vmlinux %{buildroot}/vmlinux-%{uname_r}
chmod +x %{buildroot}/vmlinux-%{uname_r}

#
# When using kernel-source package, find-debuginfo is only used to
# install the _generated_ source code (mostly arrays of data).
# Otherwise it installs both the source code and the generated one.
#
# In any cases, it generates the modules debug files, the module
# symlinks and the list of the generated source files.
#
%__debug_install_post
%define __debug_install_post %{nil}

#
# Now remove vmlinux since the build-id has been changed and doesn't
# match anymore the one embedded in the bzImage.
# Also remove the associated symlink, assuming it's the only
# dangling one.
#
rm -f %{buildroot}/vmlinux-%{uname_r}
rm -f %{buildroot}%{debuginfodir}/vmlinux-%{uname_r}.debug
sed -i -e \\,%{debuginfodir}/vmlinux-%{uname_r},d debugfiles.list

find %{buildroot}%{debuginfodir}/.build-id/ -name \*.debug | \
while read symlink
do
	symlink=${symlink%%.debug}
	readlink -e $symlink && continue
	# Dangling symlink, be sure it points to vmlinux
	case $(readlink -f $symlink) in
	%{buildroot}/vmlinux-%{uname_r})
		rm -f $symlink $symlink.debug
		sed -i -e \\,${symlink#%{buildroot}},d debugfiles.list
		break ;;
	*)
		exit 1
	esac
done

#
# Restore vmlinux with the preserved build-id. No need to create a
# separate debuginfo file and the associated symlink for now.
#
# Don't even try to install it in /boot since it includes the
# debug info.
#
mkdir -p %{buildroot}%{debuginfodir}/lib/modules/%{uname_r}
cp vmlinux %{buildroot}%{debuginfodir}/lib/modules/%{uname_r}

#
# Fix the source paths in the debug sections when not using the
# kernel-source package (including  build_srpm=0 case).
#
%if ! %{build_srpm} || ! %{no_source}
# build-id is not updated so it's not correct anymore but at least it
# still matches the one embedded in the bzImage. Actually build-id
# shouldn't be used for content verification, it's a unique identifier
# good only for matching.

# Thanks rpm5...
export PATH=/usr/lib/rpm:/usr/lib/rpm/bin:$PATH
debugedit -b %{_builddir} -d /usr/src/debug \
	%{buildroot}%{debuginfodir}/lib/modules/%{uname_r}/vmlinux
%endif
%endif

%clean
rm -rf %{buildroot}

%post
%ifarch x86_64
/sbin/installkernel %{uname_r}
%endif

%postun
%ifarch x86_64
/sbin/kernel_remove_initrd %{uname_r}
%endif

%preun
%ifarch x86_64
/sbin/installkernel -R %{uname_r}
%endif

%files -n %{name}
%defattr (-, root, root)
/boot/vmlinuz-%{uname_r}
/boot/System.map-%{uname_r}
/boot/config-%{uname_r}
/lib/modules/%{uname_r}

%if %{with devel}
%files -n %{name}-devel
%defattr (-, root, root)
%kdevel_path
%endif

%if %{with debuginfo}
%files -n %{name}-debuginfo -f debugfiles.list
%defattr (-, root, root)
%{debuginfodir}/lib/modules/%{uname_r}/vmlinux
%endif

%changelog
* Thu Mar 22 2012 Franck Bui <franck.bui@mandriva.com> 3.3.0-1.1-server
  + Mandriva Release v3.3-1
  + cpupower tools: add install target to the debug tools' makefiles
  + cpupower tools: allow to build debug tools in a separate directory too
  + cpupower tool: allow to build in a separate directory
  + cpupower tool: makefile: simplify the recipe used to generate cpupower.pot target
  + cpupower tool: remove use of undefined variables from the clean target of the top makefile
  + perf doc: allow producing documentation in a specified output directory
  + [overlayfs] fs: limit filesystem stacking depth
  + [overlayfs] overlay filesystem documentation
  + [overlayfs] implement show_options
  + [overlayfs] add statfs support
  + [overlayfs] overlay filesystem
  + [overlayfs] vfs: introduce clone_private_mount()
  + [overlayfs] vfs: export do_splice_direct() to modules
  + [overlayfs] vfs: add i_op->open()
  + [overlayfs] vfs: pass struct path to __dentry_open()
  + usb: ehci: make HC see up-to-date qh/qtd descriptor ASAP
  + Mandriva Linux boot logo.
  + media video pwc lie in proc usb devices
  + usb storage unusual_devs add id 2.6.37 buildfix
  + Change to usb storage of unusual_dev.
  + Add blacklist of usb hid modules
  + bluetooth hci_usb disable isoc transfers
  + sound alsa hda ad1884a hp dc model
  + Support a Bluetooth SCO.
  + Include kbuild export pci_ids
  + platform x86 add shuttle wmi driver
  + net netfilter psd 2.6.35 buildfix
  + ipt_psd: Mandriva changes
  + net netfilter psd
  + net netfilter IFWLOG 2.6.37 buildfix
  + IFWLOG netfilter: fix return value of ipt_IFWLOG_checkentry()
  + net netfilter IFWLOG 2.6.35 buildfix
  + netfilter ipt_IFWLOG: Mandriva changes
  + net netfilter IFWLOG
  + net sis190 fix list usage
  + gpu drm mach64 3.3 buildfix
  + gpu drm mach64 3.2 buildfix
  + gpu drm mach64 2.6.39 buildfix
  + gpu drm mach64 2.6.37 buildfix
  + gpu drm mach64 2.6.36 buildfix
  + gpu drm mach64 fix for changed drm_ioctl
  + gpu drm mach64 fix for changed drm_pci_alloc
  + gpu drm mach64 2.6.31 buildfix
  + gpu drm mach64 fixes
  + gpu drm mach64
  + agp/intel: add new host bridge id for Q57 system
  + mpt scsi modules for VMWare's emulated
  + ppscsi: build fix for 2.6.39
  + scsi megaraid new sysfs name
  + scsi ppscsi mdvbz45393
  + scsi ppscsi update for scsi_data_buffer
  + scsi ppscsi sg helper update
  + scsi ppscsi_fixes
  + scsi ppscsi-2.6.2
  + acpi video add blacklist to use vendor driver
  + acpi processor M720SR limit to C2
  + CLEVO M360S acpi irq workaround
  + acpi add proc event regs
  + acpi dsdt initrd v0.9c fixes
  + acpi dsdt initrd v0.9c 2.6.28
  + UBUNTU: SAUCE: isapnp_init: make isa PNP scans occur async
  + pnp pnpbios off by default
  + PCI: Add ALI M5229 IDE comaptibility mode quirk
  + Card bus's PCI last bus
  + x86, cpufreq: set reasonable default for scaling_min_freq with p4-clockmod
  + x86 cpufreq speedstep dothan 3
  + x86 boot video 80x25 if break
  + x86 pci toshiba equium a60 assign busses
  + kdist: make the config name part of the localversion
  + kdist: give a name to the config file
