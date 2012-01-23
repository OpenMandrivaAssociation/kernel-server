#
# Spec file generated by kdist version v0.0-28-g23fe
#
%define name		kernel-server
%define version		3.2.1

%define src_uname_r	3.2.1-2
%define uname_r		3.2.1-2.1-server%{nil}

%define source_release	2
%define build_release	1%{nil}

%define archive		kernel-server-3.2.1-2.1

%define build_srpm	1
%define no_source	1

%define source_path	/usr/src/linux-%{src_uname_r}

%define flavour		server

%define exclusive	x86_64

%define build_devel	1
%define build_debug	1

%define kdevel_path	/usr/src/devel/%{uname_r}
%ifarch x86_64
%define asm		x86_64
%define asmarch		x86
%endif
Name:			%{name}
Version:		%{version}
Release:		%mkrel %{source_release}.%{build_release}
License:		GPLv2
URL:			http://www.kernel.org
ExclusiveArch:		%{exclusive}
BuildRoot:		%{_tmppath}/%{name}-%{version}-root

%if %build_debug
%global __debug_package	1
%endif

%define debug_package	%{nil}
%define __check_files	%{nil}

Source0:		%{archive}.tar.bz2
Source1:		3.2.1-2.1-server-x86_64-defconfig
Source2:		3.2.1-2.1-server-x86-develfiles.list
Source3:		3.2.1-2.1-server-develfiles.list
Source4:		3.2.1-2.1-server-output-develfiles.list

Summary:		The Linux Kernel for Mandriva %{flavour} systems
Provides:		kernel = %{version}-%{release}
Group:			System/Kernel and hardware
Requires:		kernel-firmware
Requires(pre):		bootloader-utils
Requires(pre):		mkinitrd
Requires(pre):		module-init-tools
BuildRequires:		module-init-tools

%if %no_source
BuildRequires:		kernel-source = %{version}-%{mkrel %{source_release}}
%endif

%if %build_devel
%package devel
Summary:		The minimal Linux Kernel for building %{flavour} kernel modules
Provides:		kernel-devel = %{version}-%{release}
Group:			Development/Kernel
AutoReqProv:		no
%endif

%if %build_debug
%package debuginfo
Summary:		The debug information for the %{flavour} kernel
Provides:		kernel-debuginfo = %{version}-%{release}
Group:			Development/Debug
AutoReqProv:		no
%endif

%description -n %{name}

This kernel is compiled for server use, single or multiple processor(s)/core(s),
using no preempt, HZ_100, CFS cpu scheduler and cfq i/o scheduler.
This kernel relies on in-kernel smp alternatives to switch between up & smp
mode depending on detected hardware. To force the kernel to boot in single
processor mode, use the 'nosmp' boot parameter.


%if %build_devel
%description -n %{name}-devel
This package provides headers, makefiles and a couple of others files
sufficient to build external modules for %{name}.
%endif

%if %build_debug
%description -n %{name}-debuginfo
This package provides the %{name}'s debug information required
by some binary object tools like kgdb, perf, etc...
%endif

%prep
%if %build_srpm
%setup -q -n %{archive}
cp %{_sourcedir}/%{uname_r}-%{asm}-defconfig .config

%if %no_source
make -C %{source_path} O=$(pwd) outputmakefile
%endif

# localversion is updated here so the user can increase
# the release number anytime.
echo -n .%{build_release} >localversion

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

%if %build_devel
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
/boot
%dir /lib/modules
/lib/modules/%{uname_r}

%if %build_devel
%files -n %{name}-devel
%defattr (-, root, root)
%kdevel_path
%endif

%if %build_debug
%files -n %{name}-debuginfo -f debugfiles.list
%defattr (-, root, root)
%endif

%changelog
* Mon Jan 23 2012 Franck Bui <franck.bui@mandriva.com> 3.2.1-2.1-server
  + Mandriva Release v3.2.1-2
  + proc: clean up and fix /proc/<pid>/mem handling
  + ACPICA: Fix to allow region arguments to reference other scopes
