#include <tunables/global>

profile terraform-executor flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Allow reading from /app
  /app/** r,

  # Allow writing to /tmp only
  /tmp/** rw,

  # Allow executing terraform binary
  /usr/local/bin/terraform ix,

  # Deny everything else
  deny /** w,
  deny /proc/** w,
  deny /sys/** w,
  deny /dev/** w,

  # Network access
  network inet stream,
  network inet6 stream,

  # Capabilities (none needed)
  deny capability,
}
