const std = @import("std");
const keccak256 = @import("crypto/keccak256_accel.zig");
const clap = @import("clap");

var tid: u64 = 0;
var mutex = std.Thread.Mutex{};

pub fn main() !void {
    var output1: [32]u8 = undefined;

    keccak256.Keccak256_Accel.hash("", &output1);

    std.debug.print("test vector {x}\n", .{&output1});

    var gpa = std.heap.DebugAllocator(.{}){};
    defer _ = gpa.deinit();

    // First we specify what parameters our program can take.
    // We can use `parseParamsComptime` to parse a string into an array of `Param(Help)`.
    const params = comptime clap.parseParamsComptime(
        \\-h, --help             Display this help and exit.
        \\-n, --number <u64>   Number of trials.
        \\-b, --batch <u64>    Batch size.
        \\-r, --report <u64>   Report interval.
        \\-v, --verbosity <u64> Verbosity.
    );

    // Initialize our diagnostics, which can be used for reporting useful errors.
    // This is optional. You can also pass `.{}` to `clap.parse` if you don't
    // care about the extra information `Diagnostic` provides.
    var diag = clap.Diagnostic{};
    var res = clap.parse(clap.Help, &params, clap.parsers.default, .{
        .diagnostic = &diag,
        .allocator = gpa.allocator(),
    }) catch |err| {
        // Report useful error and exit.
        try diag.reportToFile(.stderr(), err);
        return err;
    };
    defer res.deinit();

    const n = res.args.number orelse 100000;
    const b = res.args.batch orelse 100000;
    const r = res.args.report orelse 1000000;
    const v = res.args.verbosity orelse 3;
    var timer = try std.time.Timer.start();

    while (true) {
        var output: [32]u8 = undefined;

        mutex.lock();
        const ltid = tid;
        tid = tid + b;
        mutex.unlock();

        if (ltid >= n) {
            break;
        }

        if (v >= 3 and ltid % r == 0) {
            std.debug.print("used time {}ns, hps {}\n", .{ timer.read(), 1000_000_000 * ltid / timer.read() });
        }

        for (ltid..ltid + b) |j| {
            var buf: [100]u8 = .{0} ** 100;

            std.mem.writeInt(u64, buf[92..100], j, std.builtin.Endian.big);

            // keccak256.Keccak256_Accel.hash(&buf, &output);
            std.crypto.hash.sha3.Keccak256.hash(&buf, &output, .{});

            if (v >= 5) {
                std.debug.print("key: {}, hash: {x}\n", .{ j, &output });
            }
        }
    }

    std.debug.print("used time {}ns, hps {}\n", .{ timer.read(), 1000_000_000 * n / timer.read() });
}
