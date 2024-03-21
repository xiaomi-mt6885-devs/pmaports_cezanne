# Very minimal ANSI motd
. /etc/os-release

echo
echo -e "  Welcome to \033[32mpostmarketOS $VERSION\033[0m/\033[97msystemd\033[0m! ^^\n"
echo -e "$(cat /etc/motd.ansi | sed 's/^/  /')"
